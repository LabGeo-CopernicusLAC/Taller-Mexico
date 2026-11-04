<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology|Symbology3D|Labeling|Fields|Forms|Actions|Diagrams|GeometryOptions|Relations|Legend" version="3.40.4-Bratislava">
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option value="" name="name" type="QString"/>
      <Option name="properties"/>
      <Option value="collection" name="type" type="QString"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling maxOversampling="2" zoomedInResamplingMethod="nearestNeighbour" enabled="false" zoomedOutResamplingMethod="nearestNeighbour"/>
    </provider>
    <rasterrenderer band="1" alphaBand="-1" type="paletted" opacity="1" nodataColor="">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <colorPalette>
        <paletteEntry value="4096" label="4096 - Superficies artificiales" color="#dd4a4a" alpha="255"/>
        <paletteEntry value="8192" label="8192 - Cultivos" color="#f490dd" alpha="255"/>
        <paletteEntry value="12288" label="12288 - Pastizales" color="#f9ec48" alpha="255"/>
        <paletteEntry value="16384" label="16384 - Áreas de cobertura arbórea" color="#2d8655" alpha="255"/>
        <paletteEntry value="20480" label="20480 - Áreas de cobertura arbustiva" color="#81cc71" alpha="255"/>
        <paletteEntry value="24576" label="24576 - Vegetación herbácea acuática o inundada regularmente" color="#0db59d" alpha="255"/>
        <paletteEntry value="28672" label="28672 - Manglares" color="#75d3b8" alpha="255"/>
        <paletteEntry value="32768" label="32768 - Vegetación escasa" color="#d8d79e" alpha="255"/>
        <paletteEntry value="36864" label="36864 - Suelo desnudo" color="#8c5e4c" alpha="255"/>
        <paletteEntry value="40960" label="40960 - Nieve y glaciares" color="#eaf2fa" alpha="255"/>
        <paletteEntry value="45056" label="45056 - Cuerpos de agua" color="#467ee0" alpha="255"/>
      </colorPalette>
      <colorramp name="[source]" type="randomcolors">
        <Option/>
      </colorramp>
    </rasterrenderer>
    <brightnesscontrast brightness="0" gamma="1" contrast="0"/>
    <huesaturation saturation="0" colorizeBlue="128" invertColors="0" colorizeGreen="128" colorizeStrength="100" grayscaleMode="0" colorizeRed="255" colorizeOn="0"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
