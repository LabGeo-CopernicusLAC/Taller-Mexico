"""Utilities for comparing two categorical LULC rasters for the same year."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.merge import merge
from rasterio.enums import Resampling
from rasterio.mask import mask as raster_mask
from rasterio.warp import reproject
from rasterio.warp import calculate_default_transform


def load_raster_metadata(path: str | Path) -> dict:
    """Return the metadata needed to document and compare a raster."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Raster not found: {path}")

    with rasterio.open(path) as dataset:
        values = np.ma.compressed(dataset.read(1, masked=True)).tolist()
        return {
            "path": path,
            "width": dataset.width,
            "height": dataset.height,
            "count": dataset.count,
            "dtype": dataset.dtypes[0],
            "crs": dataset.crs,
            "transform": dataset.transform,
            "resolution": dataset.res,
            "bounds": dataset.bounds,
            "nodata": dataset.nodata,
            "classes": sorted(set(values)),
        }


def validate_inputs(
    source_paths: Iterable[str | Path],
    expected_year: int = 2022,
) -> list[dict]:
    """Validate that the input rasters exist and are suitable for comparison."""
    paths = [Path(path) for path in source_paths]
    if len(paths) != 2:
        raise ValueError("Exactly two raster sources are required.")

    metadata = []
    for path in paths:
        tile_paths = find_raster_tiles(path) if path.is_dir() else [path]
        tile_metadata = [load_raster_metadata(tile_path) for tile_path in tile_paths]
        first_tile = tile_metadata[0]
        if any(item["count"] != 1 for item in tile_metadata):
            raise ValueError(f"Expected one band per raster tile: {path}")
        if any(item["crs"] is None for item in tile_metadata):
            raise ValueError(f"Raster tile has no CRS: {path}")
        if any(item["crs"] != first_tile["crs"] for item in tile_metadata):
            raise ValueError(f"Raster tiles use different CRSs: {path}")
        reference_resolution = np.asarray(first_tile["resolution"], dtype=float)
        incompatible_resolutions = [
            item["resolution"]
            for item in tile_metadata
            if not np.allclose(
                np.asarray(item["resolution"], dtype=float),
                reference_resolution,
                rtol=1e-6,
                atol=1e-9,
            )
        ]
        if incompatible_resolutions:
            resolutions = sorted(
                {tuple(round(float(value), 9) for value in item["resolution"]) for item in tile_metadata}
            )
            print(
                f"Advertencia: las teselas de {path} tienen resoluciones distintas "
                f"y serán normalizadas antes de cargarlas: {resolutions}"
            )

        metadata.append(
            {
                **first_tile,
                "path": path,
                "tiles": tile_paths,
                "classes": sorted(
                    {value for item in tile_metadata for value in item["classes"]}
                ),
            }
        )

    print(f"Validated {len(metadata)} raster sources for nominal year {expected_year}.")
    return metadata


def find_raster_tiles(folder: str | Path) -> list[Path]:
    """Find GeoTIFF tiles inside a source folder and its subfolders."""
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"Raster source folder not found: {folder}")

    tiles = sorted(
        path
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in {".tif", ".tiff"}
    )
    if not tiles:
        raise FileNotFoundError(f"No .tif or .tiff files found in: {folder}")
    return tiles


def ensure_source_crs(
    path: str | Path,
    target_crs: str,
    output_dir: str | Path,
) -> Path:
    """Return a source in target_crs, reprojecting categorical tiles if needed."""
    path = Path(path)
    target = rasterio.crs.CRS.from_user_input(target_crs)
    tile_paths = find_raster_tiles(path) if path.is_dir() else [path]

    all_tiles_match = True
    first_resolution = None
    for tile_path in tile_paths:
        with rasterio.open(tile_path) as dataset:
            if dataset.crs != target:
                all_tiles_match = False
            if first_resolution is None:
                first_resolution = dataset.res
            elif not np.allclose(dataset.res, first_resolution, rtol=1e-6, atol=1e-9):
                all_tiles_match = False
    if all_tiles_match:
        return path

    output_root = Path(output_dir) / path.name
    if output_root.resolve() == path.resolve():
        output_root = output_root.with_name(f"{output_root.name}_normalizada")
    output_root.mkdir(parents=True, exist_ok=True)

    with rasterio.open(tile_paths[0]) as reference:
        if reference.crs == target:
            target_resolution = reference.res
        else:
            reference_transform, _, _ = calculate_default_transform(
                reference.crs,
                target,
                reference.width,
                reference.height,
                *reference.bounds,
            )
            target_resolution = (
                abs(reference_transform.a),
                abs(reference_transform.e),
            )

    for tile_path in tile_paths:
        relative_path = tile_path.relative_to(path) if path.is_dir() else Path(tile_path.name)
        output_tile = output_root / relative_path
        output_tile.parent.mkdir(parents=True, exist_ok=True)

        with rasterio.open(tile_path) as source:
            if source.crs is None:
                raise ValueError(f"Raster tile has no CRS: {tile_path}")

            transform, width, height = calculate_default_transform(
                source.crs,
                target,
                source.width,
                source.height,
                *source.bounds,
                resolution=target_resolution,
            )
            profile = source.profile.copy()
            profile.update(
                crs=target,
                transform=transform,
                width=width,
                height=height,
                compress="lzw",
            )
            with rasterio.open(output_tile, "w", **profile) as destination:
                reproject(
                    source=rasterio.band(source, 1),
                    destination=rasterio.band(destination, 1),
                    src_transform=source.transform,
                    src_crs=source.crs,
                    src_nodata=source.nodata,
                    dst_transform=transform,
                    dst_crs=target,
                    dst_nodata=source.nodata,
                    resampling=Resampling.nearest,
                )

    print(f"Fuente reproyectada a {target_crs}: {output_root}")
    return output_root


def load_and_clip_raster(
    path: str | Path,
    aoi_path: str | Path | None = None,
) -> dict:
    """Read one raster or mosaic only the AOI window from a source folder."""
    path = Path(path)
    tile_paths = find_raster_tiles(path) if path.is_dir() else [path]
    datasets = [rasterio.open(tile_path) for tile_path in tile_paths]
    try:
        first_dataset = datasets[0]
        if any(dataset.count != 1 for dataset in datasets):
            raise ValueError("All raster tiles must contain exactly one band.")
        if any(dataset.crs != first_dataset.crs for dataset in datasets):
            raise ValueError("All raster tiles in a source folder must use the same CRS.")

        aoi = None
        merge_bounds = None
        if aoi_path is not None:
            import geopandas as gpd

            aoi = gpd.read_file(aoi_path)
            if aoi.empty:
                raise ValueError(f"AOI is empty: {aoi_path}")
            if aoi.crs is None:
                raise ValueError("AOI has no CRS.")
            aoi = aoi.to_crs(first_dataset.crs)
            merge_bounds = tuple(aoi.total_bounds)

        if len(datasets) == 1 and merge_bounds is None:
            array = first_dataset.read(1)
            transform = first_dataset.transform
            profile = first_dataset.profile.copy()
        else:
            mosaic, transform = merge(datasets, indexes=1, bounds=merge_bounds)
            array = mosaic[0]
            profile = first_dataset.profile.copy()
            profile.update(height=array.shape[0], width=array.shape[1], transform=transform)

        nodata = first_dataset.nodata
        profile.update(count=1, transform=transform)
    finally:
        for dataset in datasets:
            dataset.close()

    if aoi_path is not None:
        with MemoryFile() as memory_file:
            with memory_file.open(**profile) as mosaic_dataset:
                mosaic_dataset.write(array, 1)
                shapes = [
                    geometry.__geo_interface__
                    for geometry in aoi.to_crs(mosaic_dataset.crs).geometry
                ]
                clipped, transform = raster_mask(
                    mosaic_dataset,
                    shapes,
                    crop=True,
                    filled=False,
                )
                array = clipped[0].filled(nodata if nodata is not None else 0)
                profile.update(
                    height=array.shape[0],
                    width=array.shape[1],
                    transform=transform,
                )

    valid = np.ones(array.shape, dtype=bool) if nodata is None else array != nodata

    return {
        "array": array,
        "valid": valid,
        "transform": transform,
        "crs": profile["crs"],
        "nodata": nodata,
        "profile": profile,
        "path": path,
        "tiles": tile_paths,
    }


def align_to_reference(
    source: dict,
    reference: dict,
    fill_value: int | float = 0,
) -> dict:
    """Reproject a categorical raster to the reference grid using nearest neighbour."""
    destination = np.full(reference["array"].shape, fill_value, dtype=source["array"].dtype)
    reproject(
        source=source["array"],
        destination=destination,
        src_transform=source["transform"],
        src_crs=source["crs"],
        src_nodata=source["nodata"],
        dst_transform=reference["transform"],
        dst_crs=reference["crs"],
        dst_nodata=fill_value,
        resampling=Resampling.nearest,
    )

    valid_destination = np.zeros(reference["array"].shape, dtype="uint8")
    reproject(
        source=source["valid"].astype("uint8"),
        destination=valid_destination,
        src_transform=source["transform"],
        src_crs=source["crs"],
        dst_transform=reference["transform"],
        dst_crs=reference["crs"],
        dst_nodata=0,
        resampling=Resampling.nearest,
    )
    valid = valid_destination.astype(bool)

    aligned = source.copy()
    aligned.update(
        array=destination,
        valid=valid,
        transform=reference["transform"],
        crs=reference["crs"],
        profile=reference["profile"].copy(),
    )
    return aligned


def build_class_mask(
    array: np.ndarray,
    class_codes: Iterable[int | float],
    valid: np.ndarray,
) -> np.ndarray:
    """Build a boolean mask for a harmonized class."""
    return np.isin(array, list(class_codes)) & valid


def build_harmonized_raster(
    array: np.ndarray,
    valid: np.ndarray,
    harmonization: dict,
    source_key: str,
) -> tuple[np.ndarray, dict[int, str]]:
    """Encode all harmonized classes with the same integer labels across sources."""
    harmonized = np.zeros(array.shape, dtype=np.uint16)
    labels = {}
    for class_code, (class_name, mapping) in enumerate(harmonization.items(), start=1):
        labels[class_code] = class_name
        codes = mapping.get(source_key, [])
        if not codes:
            continue
        harmonized[np.isin(array, codes) & valid] = class_code
    return harmonized, labels


def summarize_harmonized_raster(
    harmonized: np.ndarray,
    valid: np.ndarray,
    labels: dict[int, str],
    area_m2: float,
) -> list[dict]:
    """Summarize area and valid-pixel percentage for every harmonized class."""
    valid_pixels = int(valid.sum())
    rows = []
    for class_code, class_name in labels.items():
        selected_pixels = int(((harmonized == class_code) & valid).sum())
        rows.append(
            {
                "codigo_homologado": class_code,
                "clase": class_name,
                "selected_pixels": selected_pixels,
                "area_ha": selected_pixels * area_m2 / 10_000,
                "percentage": 100 * selected_pixels / valid_pixels if valid_pixels else np.nan,
            }
        )
    return rows


def build_harmonized_crosswalk(
    harmonized_a: np.ndarray,
    harmonized_b: np.ndarray,
    valid_a: np.ndarray,
    valid_b: np.ndarray,
    labels: dict[int, str],
    area_m2: float,
) -> list[dict]:
    """Count spatial correspondences between harmonized classes in both sources."""
    valid = valid_a & valid_b
    rows = []
    for code_a, label_a in labels.items():
        for code_b, label_b in labels.items():
            pixels = int((valid & (harmonized_a == code_a) & (harmonized_b == code_b)).sum())
            if pixels:
                rows.append(
                    {
                        "fuente_a": label_a,
                        "fuente_b": label_b,
                        "pixeles": pixels,
                        "area_ha": pixels * area_m2 / 10_000,
                    }
                )
    return rows


def pixel_area_m2(transform, crs) -> float:
    """Return pixel area in square metres for a projected raster."""
    if crs is None or not crs.is_projected:
        raise ValueError("Area calculation requires a projected CRS in metres.")
    return abs(transform.a * transform.e - transform.b * transform.d)


def summarize_mask(mask: np.ndarray, valid: np.ndarray, area_m2: float) -> dict:
    """Summarize class area and percentage over valid pixels."""
    valid_pixels = int(valid.sum())
    selected_pixels = int((mask & valid).sum())
    area_ha = selected_pixels * area_m2 / 10_000
    percentage = 100 * selected_pixels / valid_pixels if valid_pixels else np.nan
    return {
        "valid_pixels": valid_pixels,
        "selected_pixels": selected_pixels,
        "area_ha": area_ha,
        "percentage": percentage,
    }


def build_comparison_map(
    mask_a: np.ndarray,
    mask_b: np.ndarray,
    valid_a: np.ndarray,
    valid_b: np.ndarray,
) -> np.ndarray:
    """Encode agreement and disagreement classes as integers.

    Values: 0 invalid, 1 neither, 2 both, 3 source A only, 4 source B only.
    """
    comparison = np.zeros(mask_a.shape, dtype=np.uint8)
    valid = valid_a & valid_b
    comparison[valid] = 1
    comparison[valid & mask_a & mask_b] = 2
    comparison[valid & mask_a & ~mask_b] = 3
    comparison[valid & ~mask_a & mask_b] = 4
    return comparison


def comparison_summary(comparison: np.ndarray, area_m2: float) -> dict:
    """Summarize the four comparison categories in hectares."""
    labels = {
        1: "neither",
        2: "both",
        3: "source_a_only",
        4: "source_b_only",
    }
    return {
        label: int((comparison == code).sum()) * area_m2 / 10_000
        for code, label in labels.items()
    }


def save_or_show_figure(
    figure,
    prints_dir: str | Path,
    filename: str,
    show_plots: bool = True,
) -> None:
    """Save a compact figure and optionally display it in a notebook."""
    import matplotlib.pyplot as plt

    prints_dir = Path(prints_dir)
    prints_dir.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        prints_dir / filename,
        dpi=110,
        bbox_inches="tight",
        facecolor="white",
    )
    if show_plots:
        plt.show()
    else:
        plt.close(figure)


def export_array_as_geotiff(
    array: np.ndarray,
    template: dict,
    output_dir: str | Path,
    filename: str,
    nodata: int | float | None = None,
) -> Path:
    """Export an array using the georeferencing of a loaded raster."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    profile = template["profile"].copy()
    profile.update(
        driver="GTiff",
        height=array.shape[0],
        width=array.shape[1],
        count=1,
        dtype=np.dtype(array.dtype).name,
        crs=template["crs"],
        transform=template["transform"],
        nodata=nodata,
        compress="lzw",
    )
    with rasterio.open(output_path, "w", **profile) as dataset:
        dataset.write(array, 1)
    return output_path


def export_array_as_geotiff(
    array: np.ndarray,
    template: dict,
    output_dir: str | Path,
    filename: str,
    nodata: int | float | None = None,
) -> None:
    """Export an array using the georeferencing of a loaded raster."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = template["profile"].copy()
    profile.update(
        driver="GTiff",
        height=array.shape[0],
        width=array.shape[1],
        count=1,
        dtype=np.dtype(array.dtype).name,
        crs=template["crs"],
        transform=template["transform"],
        nodata=nodata,
        compress="lzw",
    )
    with rasterio.open(output_dir / filename, "w", **profile) as dataset:
        dataset.write(array, 1)


def _categorical_image(axis, array, cmap_name: str, colorbar_label: str):
    """Render integer raster values with one stable color per category."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap

    masked_array = np.ma.masked_invalid(np.ma.asarray(array, dtype=float))
    values = np.unique(masked_array.compressed())
    if values.size == 0:
        values = np.array([0])
    base_cmap = plt.get_cmap(cmap_name, values.size)
    cmap = ListedColormap(base_cmap(np.arange(values.size)))
    norm = BoundaryNorm(np.arange(values.size + 1) - 0.5, values.size)
    image = axis.imshow(
        masked_array,
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
        resample=False,
    )
    axis.set_axis_off()
    colorbar = axis.figure.colorbar(image, ax=axis, ticks=np.arange(values.size))
    colorbar.ax.set_yticklabels([str(int(value)) for value in values])
    colorbar.set_label(colorbar_label)
    return image


def plot_source_pair_for_workshop(
    source_a: dict,
    source_b: dict,
    source_a_label: str,
    source_b_label: str,
    source_a_cmap: str,
    source_b_cmap: str,
    prints_dir: str | Path,
    raster_dir: str | Path,
    show_plots: bool = True,
) -> None:
    """Compare original source codes and export both source rasters."""
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, 2, figsize=(13, 6), constrained_layout=True, dpi=160)
    for axis, source, label, cmap in zip(
        axes,
        (source_a, source_b),
        (source_a_label, source_b_label),
        (source_a_cmap, source_b_cmap),
    ):
        array = np.ma.masked_where(~source["valid"], source["array"])
        _categorical_image(axis, array, cmap, "Código original")
        axis.set_title(label)
    figure.suptitle("Fuentes originales antes de la homogenización")
    save_or_show_figure(figure, prints_dir, "01_fuentes_originales.png", show_plots)
    export_array_as_geotiff(
        source_a["array"], source_a, raster_dir, "01_fuente_a_original.tif", source_a["nodata"]
    )
    export_array_as_geotiff(
        source_b["array"], source_b, raster_dir, "01_fuente_b_original.tif", source_b["nodata"]
    )


def plot_harmonized_pair_for_workshop(
    mask_a: np.ndarray,
    mask_b: np.ndarray,
    source_a_label: str,
    source_b_label: str,
    target_class: str,
    class_color: str,
    source_a_template: dict,
    source_b_template: dict,
    prints_dir: str | Path,
    raster_dir: str | Path,
    show_plots: bool = True,
) -> None:
    """Compare both binary masks with the same harmonized-class palette."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap

    figure, axes = plt.subplots(1, 2, figsize=(13, 6), constrained_layout=True, dpi=160)
    cmap = ListedColormap(["white", class_color])
    for axis, mask, label in zip(
        axes, (mask_a, mask_b), (source_a_label, source_b_label)
    ):
        axis.imshow(mask, cmap=cmap, interpolation="nearest", vmin=0, vmax=1, resample=False)
        axis.set_title(f"{label}: {target_class}")
        axis.set_axis_off()
    figure.suptitle("Después de homologar la clase")
    save_or_show_figure(figure, prints_dir, "02_clase_homologada.png", show_plots)
    export_array_as_geotiff(
        mask_a.astype(np.uint8),
        source_a_template,
        raster_dir,
        "02_mascara_fuente_a.tif",
    )
    export_array_as_geotiff(
        mask_b.astype(np.uint8),
        source_b_template,
        raster_dir,
        "02_mascara_fuente_b.tif",
    )


def plot_comparison_for_workshop(
    comparison: np.ndarray,
    template: dict,
    raster_dir: str | Path,
    prints_dir: str | Path,
    show_plots: bool = True,
) -> None:
    """Display and save the four-category agreement map."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    colors = ["white", "lightgray", "forestgreen", "darkorange", "royalblue"]
    labels = ["Sin datos", "Ninguna", "Ambas", "Solo fuente A", "Solo fuente B"]
    figure, axis = plt.subplots(figsize=(10, 7), constrained_layout=True, dpi=180)
    axis.imshow(
        comparison,
        cmap=ListedColormap(colors),
        interpolation="nearest",
        resample=False,
        vmin=0,
        vmax=4,
    )
    axis.set_title("Coincidencias y desacuerdos")
    axis.set_axis_off()
    handles = [Patch(color=color, label=label) for color, label in zip(colors, labels)]
    axis.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=3)
    save_or_show_figure(figure, prints_dir, "03_coincidencias_desacuerdos.png", show_plots)
    export_array_as_geotiff(
        comparison.astype(np.uint8),
        template,
        raster_dir,
        "03_coincidencias_desacuerdos.tif",
        nodata=0,
    )


def plot_mask_pair(
    mask_a: np.ndarray,
    mask_b: np.ndarray,
    source_a_label: str,
    source_b_label: str,
    class_color: str = "forestgreen",
) -> None:
    """Plot the selected class mask for both sources."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap

    figure, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    cmap = ListedColormap(["white", class_color])
    for axis, mask, label in zip(axes, (mask_a, mask_b), (source_a_label, source_b_label)):
        axis.imshow(mask, cmap=cmap, interpolation="none", vmin=0, vmax=1)
        axis.set_title(label)
        axis.set_axis_off()
    plt.show()


def plot_source_raster_pair(
    source_a: dict,
    source_b: dict,
    source_a_label: str,
    source_b_label: str,
    source_a_cmap: str = "viridis",
    source_b_cmap: str = "magma",
) -> None:
    """Plot the original categorical rasters with source-specific palettes."""
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)
    for axis, source, label, cmap in zip(
        axes,
        (source_a, source_b),
        (source_a_label, source_b_label),
        (source_a_cmap, source_b_cmap),
    ):
        array = np.ma.masked_where(~source["valid"], source["array"])
        image = axis.imshow(array, cmap=cmap, interpolation="none")
        axis.set_title(label)
        axis.set_axis_off()
        figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04, label="Código original")
    figure.suptitle("Fuentes originales antes de la homogenización")
    plt.show()


def plot_comparison_map(comparison: np.ndarray) -> None:
    """Plot agreement and disagreement categories."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    colors = ["white", "lightgray", "forestgreen", "darkorange", "royalblue"]
    labels = ["Sin datos", "Ninguna", "Ambas", "Solo fuente A", "Solo fuente B"]
    figure, axis = plt.subplots(figsize=(8, 6), constrained_layout=True)
    axis.imshow(comparison, cmap=ListedColormap(colors), interpolation="none", vmin=0, vmax=4)
    axis.set_title("Coincidencias y desacuerdos entre fuentes")
    axis.set_axis_off()
    handles = [Patch(color=color, label=label) for color, label in zip(colors, labels)]
    axis.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=3)
    plt.show()
