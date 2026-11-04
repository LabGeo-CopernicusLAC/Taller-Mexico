<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.42.0-Münster" styleCategories="Symbology">
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option name="name" type="QString" value=""/>
      <Option name="properties"/>
      <Option name="type" type="QString" value="collection"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling zoomedInResamplingMethod="nearestNeighbour" enabled="false" maxOversampling="2" zoomedOutResamplingMethod="nearestNeighbour"/>
    </provider>
    <rasterrenderer alphaBand="-1" band="1" type="paletted" nodataColor="" opacity="1">
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
        <paletteEntry label="4368 - Residencial" color="#fcdb72" value="4368" alpha="255"/>
        <paletteEntry label="4384 - Comercial/Industrial" color="#cd6667" value="4384" alpha="255"/>
        <paletteEntry label="4400 - Edificios" color="#9986f7" value="4400" alpha="255"/>
        <paletteEntry label="4624 - Calles y ferrocarriles" color="#dfdfdf" value="4624" alpha="255"/>
        <paletteEntry label="4640 - Aeropuertos" color="#676767" value="4640" alpha="255"/>
        <paletteEntry label="5136 - Vegetación boscosa" color="#52a53d" value="5136" alpha="255"/>
        <paletteEntry label="5152 - Agricultura" color="#f490dd" value="5152" alpha="255"/>
        <paletteEntry label="5168 - Recreación" color="#ff5f5f" value="5168" alpha="255"/>
        <paletteEntry label="5184 - Otros espacios abiertos" color="#8c5e4c" value="5184" alpha="255"/>
        <paletteEntry label="36880 - Extracción de minerales" color="#fca55e" value="36880" alpha="255"/>
        <paletteEntry label="45056 - Cuerpos de agua" color="#467ee0" value="45056" alpha="255"/>
      </colorPalette>
      <colorramp name="[source]" type="randomcolors">
        <Option/>
      </colorramp>
    </rasterrenderer>
    <brightnesscontrast gamma="1" brightness="0" contrast="0"/>
    <huesaturation saturation="0" colorizeRed="255" colorizeGreen="128" colorizeBlue="128" grayscaleMode="0" colorizeStrength="100" invertColors="0" colorizeOn="0"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
