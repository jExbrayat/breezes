# Data sources: thermal-breeze model, French Alps

Tested 2026-10-26 from this machine with `curl -I`, small range requests, and tiny WFS/STAC/REST queries.
**Verified = y** means an HTTP 200 or a successful query came back during that test.
**UNVERIFIED** means the item was not tested or could not be reached. No large files were downloaded. Test files are in
`/tmp/claude-1000/-home-jules-Desktop-breezes/37774ad5-1fcb-4f18-b74d-cc04eea7e598/scratchpad/datasrc_test/` (~10 MB, mostly two catalogue documents).
Bounding box used for the French Alps: lon 5–8°E, lat 43.5–46.5°N.

---

## 1. Phase-2 surface data

### 1a. Land cover: ESA WorldCover and CORINE

| dataset | access URL / pattern | auth? | resolution / CRS | licence | verified |
|---|---|---|---|---|---|
| ESA WorldCover 2021 v200 (map) | `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{TILE}_Map.tif` (also `s3://esa-worldcover/...`, anonymous). 3°×3° tiles named by the SW corner. The Alps need `N42E003, N42E006, N45E003, N45E006` (70/51/102/106 MB). Tile index: `v200/2021/esa_worldcover_grid.geojson` | no | 1/12000° (≈9.3 m N-S, ≈6.5 m E-W at 45°N), EPSG:4326, COG (1024² blocks, deflate), uint8, nodata 0. Classes: 10 tree, 20 shrub, 30 grass, 40 crop, 50 built, 60 bare, 70 snow/ice, 80 water, 90 wetland, 100 moss | CC BY 4.0 | y (header parsed) |
| CORINE LC 2018, vector, EEA ArcGIS REST | `https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_WM/MapServer/0/query?where=1%3D1&geometry={xmin},{ymin},{xmax},{ymax}&geometryType=esriGeometryEnvelope&inSR=4326&outSR=4326&outFields=Code_18&f=geojson`. At most 1000 features per call; page with `resultOffset`. Covers FR, CH and IT | no | 25 ha MMU, 100 m positional accuracy | Copernicus free & open, attribution "© EU, Copernicus Land Monitoring Service 2018, EEA" | y |
| CORINE LC 2018, France, IGN download | `https://data.geopf.fr/telechargement/download/CORINELANDCOVER/CLC18_SHP__FRA_2018/CLC18_SHP__FRA_2018.7z` (318 MB). Also listed in the Atom feed `.../resource/CORINELANDCOVER`: `CLC_1-0__GPKG_WGS84G_FXX_2018-01-01` (320 MB) and `CLC_1-0__TIF_WGS84G_FXX_2018-01-01` (10 MB raster; resolution not checked) | no | vector (SHP CRS not checked; probably Lambert-93) | as above | y (SHP HEAD); GPKG/TIF y (listed only) |
| CORINE LC 2018, France, IGN WFS | `https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=LANDCOVER.CLC18_FR:clc18_fr&BBOX={latmin},{lonmin},{latmax},{lonmax},urn:ogc:def:crs:EPSG::4326&OUTPUTFORMAT=application/json` (output defaults to EPSG:2154; add `&SRSNAME=EPSG:4326`) | no | as above | as above | y |
| CORINE, official CLMS portal | land.copernicus.eu → dataset download | EU Login (UNVERIFIED) | 100 m raster / vector | as above | page y, download UNVERIFIED |

**Recommended:** use WorldCover 2021 tiles from S3 as the main 10 m class map. CORINE has a 25 ha minimum mapping unit, which is too coarse for small lakes and glacier tongues. Use it only as a secondary urban/agriculture layer, queried through the EEA REST endpoint. That endpoint needs no account and covers both sides of the border.

### 1b. Glaciers

| dataset | access URL / pattern | auth? | resolution / CRS | licence | verified |
|---|---|---|---|---|---|
| RGI 7.0 (NSIDC-0770), region 11 Central Europe | `https://daacdata.apps.nsidc.org/pub/DATASETS/nsidc0770_rgi_v7/...` (the exact regional file name is UNVERIFIED, behind the auth wall) | **Earthdata login** (401 returned) | polygons, EPSG:4326 | CC BY 4.0 | n (401) |
| GLIMS WFS, layer `GLIMS:RGI_CentralEurope` | `https://www.glims.org/geoserver/ows?service=WFS&version=2.0.0&request=GetFeature&typeNames=GLIMS:RGI_CentralEurope&bbox={latmin},{lonmin},{latmax},{lonmax},urn:ogc:def:crs:EPSG::4326&outputFormat=application/json`. **Returns RGI 6.0** (IDs `RGI60-11.*`, outlines c. 2003) | no | polygons, EPSG:4326 | GLIMS/RGI terms (attribution) | y |
| GLIMS WFS, layer `GLIMS:GLIMS_Glacier_Outlines` | same endpoint and `typeNames`. Multi-temporal outlines, 1939–2022 near Mont Blanc. Filter on `src_date` and `line_type=glac_bound` | no | polygons | GLIMS terms | y |
| Paul et al. Sentinel-2 Alps inventory 2015/16 (PANGAEA 909133) | `https://store.pangaea.de/Publications/PaulF-etal_2019/c3s_gi_rgi11_s2_2015_v2.zip` (7.8 MB; one shapefile covering the whole Alps) | no | polygons, **EPSG:32632** (UTM 32N, `.prj` read) | CC BY 4.0 | y (zip directory and .prj read) |
| IGN BD TOPO, glaciers (France only) | WFS `TYPENAMES=BDTOPO_V3:surface_hydrographique`, filter `nature='Glacier, névé'` | no | ~1:10k vector | Licence Ouverte 2.0 | y |

**Recommended:** the PANGAEA Sentinel-2 2015/16 inventory. It is free, needs no account, covers the whole Alps and is recent. I did not verify whether RGI 7.0 region 11 is built from this inventory. Use the GLIMS WFS `src_date ≥ 2015` outlines, or the BD TOPO glaciers, for more recent French outlines. RGI 7 is only worth getting if someone already has an Earthdata account.

### 1c. Lakes / water

| dataset | access URL / pattern | auth? | resolution | licence | verified |
|---|---|---|---|---|---|
| HydroLAKES v1.0 | `https://data.hydrosheds.org/file/hydrolakes/HydroLAKES_polys_v10_shp.zip` (820 MB, global). The site also lists `HydroLAKES_polys_v10.gdb.zip` (untested) | no | lakes ≥ 10 ha, EPSG:4326 | CC BY 4.0 | y (SHP) |
| IGN BD TOPO `plan_d_eau` (France) | `https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=BDTOPO_V3:plan_d_eau&BBOX=...&OUTPUTFORMAT=application/json` (returned "Lac d'Annecy") | no | ~1:10k | Licence Ouverte 2.0 | y |
| OSM via Overpass | `POST https://overpass-api.de/api/interpreter` with `data=[out:json];way["natural"="water"](S,W,N,E);...` | no | OSM | ODbL | y (first try returned "at capacity"; retry OK) |
| OSM Geofabrik extracts | `https://download.geofabrik.de/europe/france/rhone-alpes-latest.osm.pbf` (532 MB), `.../provence-alpes-cote-d-azur-latest.osm.pbf` (391 MB), `https://download.geofabrik.de/europe/switzerland-latest.osm.pbf` (549 MB) | no | OSM | ODbL | y |
| (not usable) osmdata water polygons | `https://osmdata.openstreetmap.de/download/water-polygons-split-4326.zip`: **oceans and seas only, no lakes** | — | — | ODbL | y (but not useful) |

**Recommended:** BD TOPO `plan_d_eau` over WFS for France, plus Overpass (or a Geofabrik extract) for CH/IT. WorldCover class 80 is a consistent 10 m raster fallback. HydroLAKES is not worth an 820 MB download for this domain.

### 1d. Broadband albedo / reflectance

| dataset | access URL / pattern | auth? | resolution | licence | verified |
|---|---|---|---|---|---|
| MODIS MCD43A3 v061 (BSA/WSA shortwave) | Search: `https://cmr.earthdata.nasa.gov/search/granules.json?short_name=MCD43A3&version=061&bounding_box=5,43.5,8,46.5&temporal=...` (no auth). Data: `https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MCD43A3.061/{granule}/{granule}.hdf`. Tile **h18v04** covers the whole domain | **Earthdata login** for data (GET returned 401) | 500 m daily, sinusoidal, HDF4 | NASA open data | search y / data n |
| MODIS MCD43A4 NBAR on MS Planetary Computer | STAC `https://planetarycomputer.microsoft.com/api/stac/v1/collections/modis-43A4-061`. Assets are COGs; sign each with `https://planetarycomputer.microsoft.com/api/sas/v1/sign?href={asset}` (anonymous) | no (anonymous SAS) | 500 m, 7 bands. Nadir reflectance, not albedo (narrow-to-broadband conversion gives an approximation) | NASA open | y |
| Copernicus / C3S surface albedo | CDS `https://cds.climate.copernicus.eu/datasets/satellite-albedo` (1 km and 300 m, 10-daily). The VITO manifest host `globalland.vito.be` timed out | CDS account + API key | 300 m–1 km, too coarse for valleys | Copernicus | page y, data UNVERIFIED |
| Sentinel-2 L2A COGs (Element 84 earth-search) | STAC `POST https://earth-search.aws.element84.com/v1/search` with collections `sentinel-2-l2a` or `sentinel-2-c1-l2a` (reprocessed Collection 1). Asset examples: `https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/31/T/GL/2023/8/S2B_31TGL_20230822_0_L2A/B04.tif` and `https://e84-earth-search-sentinel-data.s3.us-west-2.amazonaws.com/sentinel-2-c1-l2a/31/T/GL/2024/8/S2A_T31TGL_20240831T103023_L2A/B04.tif`. Asset keys: blue, green, red, nir, swir16, swir22, scl… The Chamonix bbox returned MGRS 31TGL, 31TGM and 32TLR; find the others by bbox search | no | 10/20 m, UTM 31N/32N (EPSG 32631/32632) | Copernicus Sentinel data, free; credit "Contains modified Copernicus Sentinel data" | y |
| ESA WorldCover S2 annual median composites (2020, 2021) | `https://esa-worldcover-s2.s3.eu-central-1.amazonaws.com/rgbnir/2021/N45/ESA_WorldCover_10m_2021_v200_N45E006_S2RGBNIR.tif` (4×uint16 B04,B03,B02,B08; ~565 MB) and `.../swir/2021/N45/ESA_WorldCover_10m_2021_v200_N45E006_SWIR.tif` (2×uint8 B11,B12 median, scale 0.004; 43 MB). Tiles are **1°×1°**, named by SW corner; an `ndvi/` prefix also exists | no | 10 m (RGBNIR), 20 m (SWIR), EPSG:4326 | CC BY 4.0 (in the file metadata) | y (headers read) |
| EOX Sentinel-2 cloudless | `https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024_3857/default/g/{z}/{y}/{x}.jpg` | no | RGB JPEG only, **not radiometric**; display use only | CC BY-NC-SA 4.0 (commercial use needs an EOX licence) | y |

**Recommended:** compute broadband albedo from Sentinel-2 L2A. The six bands B2/B3/B4/B8/B11/B12 used by standard narrow-to-broadband formulas, e.g. Bonafoni & Sekertekin 2020 (UNVERIFIED citation), are all available:
- a static "typical" map from the WorldCover 2021 median composites, which need no account;
- monthly or seasonal maps from earth-search scenes.

Use MCD43A3 only if someone gets a free Earthdata account (500 m daily, useful as a cross-check).

### 1e. Snow cover

| dataset | access URL / pattern | auth? | resolution | licence | verified |
|---|---|---|---|---|---|
| Copernicus HR-S&I FSC / GFSC / PSA | Finder `https://cryo.land.copernicus.eu/finder/` (page 200, but the `resto` search API returned 503). WEkEO HDA needs an account. Production ended; per CLMS the 2016–Jan 2025 archive stays on Finder/WEkEO, and NRT data since Jan 2025 is "via S3 buckets" (bucket URL UNVERIFIED) | account (WEkEO) | 20 m FSC daily; 60 m gap-filled | Copernicus | partial / UNVERIFIED |
| Theia snow (Let It Snow, CNES) | `theia.cnes.fr/atdistrib/rocket/` now redirects to `https://geodes.cnes.fr/`. GEODES STAC calls returned errors | account (UNVERIFIED) | 20 m | Etalab (UNVERIFIED) | n |
| MODIS MOD10A1/MYD10A1 v061 on Planetary Computer | STAC collections `modis-10A1-061` (daily; assets `NDSI_Snow_Cover`, `Snow_Albedo_Daily_Tile`, QA) and `modis-10A2-061` (8-day). Example COG `https://modiseuwest.blob.core.windows.net/modis-061-cogs/MYD10A1/18/04/2024034/...NDSI_Snow_Cover.tif`, signed via `/api/sas/v1/sign?href=` | no (anonymous SAS) | 500 m daily | NASA open | y (signed GET 200) |
| Sentinel-2 SCL (class 11 = snow/ice) | earth-search asset `scl` (e.g. `.../S2B_31TGL_20230822_0_L2A/SCL.tif`, 3 MB) | no | 20 m, per scene | Copernicus | y |

**Recommended:** build monthly snow-frequency maps from the Sentinel-2 SCL band (20 m, no account). Add MODIS 10A1 from Planetary Computer for daily snow-line context. Treat HR-S&I as optional; it needs an account and production has ended.

### 1f. Forest / vegetation

| dataset | access URL / pattern | auth? | resolution | licence | verified |
|---|---|---|---|---|---|
| Copernicus HRL Tree Cover Density 2018, EEA ImageServer | `https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/exportImage?bbox={W},{S},{E},{N}&bboxSR=4326&imageSR=3035&size={w},{h}&format=tiff&pixelType=U8&interpolation=RSP_NearestNeighbor&f=image`. Returns raw 0–100 % values, max 15000 px per side; tile requests for larger areas | no | 10 m (service in EPSG:3857; any output SR) | Copernicus | y (60×60 GeoTIFF returned) |
| Sibling HRL ImageServers, same folder | `HRL_DominantLeafType2018`, `HRL_Grassland_2018`, `HRL_ImperviousnessDensity_2018`, `HRL_WaterWetness_2018`, `HRL_SmallWoodyFeatures_2021` | no | 10 m (SWF 5 m) | Copernicus | y (listed) |
| HRL via the CLMS portal | land.copernicus.eu product pages | EU Login (UNVERIFIED) | 10 m | Copernicus | page y |
| Hansen Global Forest Change, `treecover2000` | `https://storage.googleapis.com/earthenginepartners-hansen/GFC-2024-v1.12/Hansen_GFC-2024-v1.12_treecover2000_50N_000E.tif` (374 MB, 10°×10° tile) | no | 30 m; year-2000 baseline | CC BY 4.0 | y |
| IGN BD Forêt v2 / BD TOPO vegetation | WFS `LANDCOVER.FORESTINVENTORY.V2:formation_vegetale` and `BDTOPO_V3:zone_de_vegetation` (classes such as "Forêt fermée de conifères"). Bulk: `https://data.geopf.fr/telechargement/resource/BDFORET` | no | 0.5 ha vector | Licence Ouverte 2.0 | y |

**Recommended:** HRL TCD 2018 from the EEA ImageServer (10 m, no account, Pan-European). Add the HRL Dominant Leaf Type layer for the conifer/broadleaf split (relevant for winter albedo). Use BD Forêt v2 for French forest typology if needed.

---

## 2. Independent validation data (hold out from fitting)

### 2a. Météo-France hourly climatological data (data.gouv.fr)

| item | URL / pattern | auth? | licence | verified |
|---|---|---|---|---|
| dataset page / API | `https://www.data.gouv.fr/api/1/datasets/donnees-climatologiques-de-base-horaires/` (1463 resources; read `resources[].url`) | no | Licence Ouverte 2.0 | y |
| files | `https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/HOR/H_{DEP}_{PERIOD}.csv.gz`. DEP ∈ 73, 74, 38, 05, 04, 06, 26. PERIOD ∈ `…`, `2000-2009`, `2010-2019`, `previous-2020-2024`, `latest-2025-2026`. Dept 73 sizes: 55 / 99 / 56 / 19 MB. **The previous/latest names roll over each year, so discover them through the API** | no | LO 2.0 | y |
| field description | `.../BASE/HOR/H_descriptif_champs.csv` | no | — | y |
| station list | dataset `informations-sur-les-stations-metadonnees`, CSV `observations-liste-stations-obs-metropole-om-*.csv` (dated name: discover via API); full `fiches.json` is 200 MB | no | LO 2.0 | y |
| single-station query without downloading a department file | `https://tabular-api.data.gouv.fr/api/resources/{resource_id}/data/?NUM_POSTE__exact=74056001&AAAAMMJJHH__greater=2025070100&columns=AAAAMMJJHH,FF,DD,QFF,QDD` (also supports `__groupby` / `__count`) | no | — | y (worked even on the 99 MB file) |

Format: `;`-separated, one row per station-hour.
- `AAAAMMJJHH` is in **UTC**. I checked this indirectly: global radiation at St-Geoirs on 21 Jun 2025 peaks at labels 12–13, which matches UTC with the label at the end of the hour.
- **FF**: 10-min mean wind at 10 m at the top of the hour (m/s, 0.1 precision). **DD**: its direction (°).
- **FXY / DXY / HXY**: max 10-min mean within the hour, with its direction and time. **FXI / DXI / HXI**: max instantaneous gust. **FXI3S / DXI3S**: 3-s gust.
- **FF2 / DD2 / FXI2 / DXI2**: the same at 2 m, where present.
- Each field `X` has a quality column `QX`: 0 protected, 1 validated, 2 doubtful, 9 filtered only.
- `T`, `GLO` and `INS` are useful for selecting sunny, synoptically calm days.

Valley-floor stations, checked in `latest-2025-2026` with `FF__count > 1000` unless noted:

| NUM_POSTE | name | alt (m) | setting |
|---|---|---|---|
| 38384001 | GRENOBLE-ST GEOIRS | 384 | Bièvre plain, outside the Alpine valleys: plain/control station |
| 38538002 | GRENOBLE - LVD (Le Versoud) | 220 | Grésivaudan valley floor |
| 38185012 | GRENOBLE-CEA-RADOME | 213 | Grenoble city, Isère/Drac junction |
| 73329001 | CHAMBERY-AIX (Voglans) | 235 | Lac du Bourget / Chambéry cluse |
| 74182001 | MEYTHET (Annecy) | 455 | Annecy basin, 3 km from the lake |
| 73297003 | ALBERTVILLE | 314 | Isère/Arly confluence (open since 2020) |
| 73171002 | MONTMELIAN | 264 | Combe de Savoie |
| 73054001 | BOURG ST MAURICE | 865 | upper Tarentaise |
| 73255003 | STE MARIE CUINES | 460 | lower Maurienne. **Substitute for St-Jean-de-Maurienne 73248002, which has no wind in any period** |
| 74056001 | CHAMONIX | 1042 | Arve valley |
| 74042003 | BONNEVILLE | 453 | lower Arve |
| 05046001 | EMBRUN | 873 | Durance |
| 05136002 | ST CREPIN | 906 | upper Durance (Mont-Dauphin) |
| 05023001 | BRIANCON | — | **wind only in the 2000-2009 file**; nothing after 2009 |
| 05061009 / 04019001 / 04049001 / 04209005 | GAP / BARCELONNETTE / ST AUBAN / SISTERON | 885 / 1155 / 458 / 500 | Southern Alps valleys |
| 74056006 / 73144001 / 05079402 | AIGUILLE DU MIDI / MONT CENIS / GALIBIER-NIVOSE | 3845 / 2032 / 2559 | crest stations, for screening out synoptic-wind days |

### 2b. MeteoSwiss open data (Valais / Chablais)

| item | URL / pattern | auth? | licence | verified |
|---|---|---|---|---|
| STAC collection | `https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn` (items = station abbreviations) | no | CC BY (MeteoSwiss OGD) | y |
| hourly CSV | `https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/{abbr}/ogd-smn_{abbr}_h_historical_2020-2029.csv`. Also `_h_recent`, `_h_now`, and `_t_` (10-min) files; Sion is 7.5 MB | no | CC BY | y |
| metadata | `.../ogd-smn_meta_stations.csv`, `.../ogd-smn_meta_parameters.csv` | no | CC BY | y |

The CSVs are `;`-separated, with `reference_timestamp` as `dd.mm.yyyy HH:MM` in **UTC**. I checked this indirectly: Sion `gre000h0` on 16–17 Aug 2020 is symmetric around about 11:30 UTC, which is solar noon there.
- `fkl010h0`: hourly mean wind speed, m/s.
- `dkl010h0`: hourly mean direction.
- `fkl010h1`: 1-s gust, hourly max.
- 10-min equivalents: `fkl010z0` / `dkl010z0`.

Valais/Chablais stations: **SIO** Sion, **VIS** Visp, **EVI** Evionnaz, **AIG** Aigle (Chablais), **BOU** Bouveret (Léman shore), **ULR** Ulrichen, **ZER** Zermatt, **EVO** Evolène, **MVE** Montana (slope), **GSB** Gd-St-Bernard (pass), **ATT** Les Attelas (ridge), **MAR**, **MOB**, **BLA**.

**Recommended (2a + 2b):** use the station tables above. Pull single stations through the tabular API (FR) and per-station CSVs (CH). Keep the crest stations only for filtering out synoptically forced days.

### 2c. Published breeze maps

| source | access | machine-readable? | licence | verified |
|---|---|---|---|---|
| G. Briffe, "Brises et Confluences Alpes du Sud" | from `http://gabriel.briffe.free.fr/`: `https://drive.google.com/file/d/17E5ArGSrJ35K8ipxjj43GzCnW8N3_x1A/view` (`confluencesFrancais.pptx`); English: `.../1Hx-fIiQ9G4ou6xbyTi843RsN17OdHftl/view` (`convergencesEnglish.pptx`) | **No.** PowerPoint slides with drawn arrows; needs **manual digitizing** | not stated; ask the author | y |
| "Carte suisse des brises" | not found in web search | — | — | UNVERIFIED (need a link) |
| PNR Bauges / Chartreuse / Vercors free-flight breeze maps | not found online | probably PDF/print, so manual digitizing | — | UNVERIFIED |
| "Karlis" breeze video | not found | video, so manual digitizing only | — | UNVERIFIED (need a link) |
| FSVL site information boards | e.g. `https://www.shv-fsvl.ch/fileadmin/files/redakteure/Allgemein/Sicherheit/SHVInfotafeln/Evolene.pdf` (qualitative valley-wind notes per site) | text, manual | — | UNVERIFIED (search hit only) |
| thermal.kk7.ch thermal / skyway maps | tiles `https://thermal.kk7.ch/tiles/skyways_all_all/{z}/{x}/{-y}.png?src={app}` (**TMS y**; e.g. `thermals_jul_07`). Hotspot export as CSV/GPX/CUP on the site | raster tiles plus hotspot CSV. Derived from XContest/Leonardo tracks, so this is a thermal proxy, not surface breeze | CC BY-NC-SA 4.0 | y |

**Recommended:** digitize Briffe's slides into a small GeoJSON of breeze/convergence arrows as qualitative validation. Use kk7 hotspots as an independent check of the phase-1 heating/trigger logic. Ask the user for links to the Swiss map, the PNR maps and the Karlis video.

### 2d. Paragliding track archives

| source | access | terms | verified |
|---|---|---|---|
| XContest | `www.xcontest.org`. IGC download needs a login; `robots.txt` disallows `/track.php` and the flight-search pages | no public API, so **do not scrape**; ask XContest for a data agreement | y (robots) |
| Leonardo (paraglidingforum.com) | `https://www.paraglidingforum.com/leonardo/`. Per-flight IGC links (login requirement UNVERIFIED); `robots.txt` `Crawl-delay: 30` | terms not found; ask before bulk use | y (site) |

Thermalling-circle drift gives the wind **at thermal altitude** (hundreds of m AGL), not the surface breeze. Use it with care.

**Recommended:** do not build on track archives without written permission. kk7 (2c) already gives an aggregated, licensed derivative.

---

## 3. Basemaps for Leaflet (no API key)

All templates below returned 200 for a z12 tile over Chamonix (z12/x2126/y1459).

| layer | Leaflet URL template | max z | attribution / licence | caveats |
|---|---|---|---|---|
| OpenTopoMap | `https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png` (s=a,b,c) | 17 | "Kartendaten: © OpenStreetMap-Mitwirkende, SRTM \| Kartendarstellung: © OpenTopoMap (CC-BY-SA)" | no mass downloading, no uptime guarantee |
| IGN Plan IGN v2 | `https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png` | 19 | "© IGN – Géoplateforme", Licence Ouverte 2.0 | France-centric. `TILEMATRIXSET=PM` and `PM_0_19` both work |
| IGN orthophoto | same, `LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&FORMAT=image/jpeg` | 19 | "© IGN" | — |
| IGN shaded relief | same, `LAYER=ELEVATION.ELEVATIONGRIDCOVERAGE.SHADOW&STYLE=estompage_grayscale&FORMAT=image/png` | 15 | "© IGN" | good overlay at 0.4 opacity |
| IGN mountain slopes (>30°) | same, `LAYER=GEOGRAPHICALGRIDSYSTEMS.SLOPES.MOUNTAIN&STYLE=normal&FORMAT=image/png` | 17 | "© IGN" | handy for the slope-breeze layer |
| IGN SCAN Régional | same, `LAYER=IGNF_CARTES_SCAN-REGIONAL&STYLE=SCANREG&FORMAT=image/jpeg` | 12 | "© IGN" | the only open SCAN layer besides SCAN 1000 and historical maps |
| IGN SCAN 25 | `GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR` returns "Layer unknown" on the open endpoint | — | — | **needs an API key** (private endpoint, not tested) |
| IGN CORINE 2018 | same, `LAYER=LANDCOVER.CLC18&STYLE=CORINE%20Land%20Cover&FORMAT=image/png` | 16 | "© IGN / Copernicus" | display only |
| Esri World Shaded Relief | `https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}` | 13 | "Tiles © Esri — Source: Esri" | Esri terms at goto.arcgisonline.com/maps/World_Shaded_Relief (commercial limits UNVERIFIED) |
| CARTO light / voyager | `https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png` (also `rastertiles/voyager`) | 20 | "© OpenStreetMap contributors, © CARTO" | keyless worked, **but carto.com/basemaps now issues keys (`?key=`)**: 5 M req/month non-commercial, 1 M commercial. Keyless access may be withdrawn |
| swisstopo colour map | `https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/3857/{z}/{x}/{y}.jpeg` | ~18 | "© swisstopo" (free OGD) | CH plus border fringe |
| OSM standard | `https://tile.openstreetmap.org/{z}/{x}/{y}.png` | 19 | "© OpenStreetMap contributors" | OSMF tile policy: light use only, valid Referer/UA |
| EOX S2 cloudless 2024 | `https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024_3857/default/g/{z}/{y}/{x}.jpg` | ~15 | "EOxCloudless https://cloudless.eox.at by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2024)" | CC BY-NC-SA 4.0, non-commercial |

**Recommended:** use OpenTopoMap as the default base layer, with IGN Plan IGN v2 and IGN orthophoto as alternatives (no key, open licence, best detail in France). Add IGN shaded relief or the slopes layer as overlays, and swisstopo for the Valais. Avoid relying on CARTO staying keyless; it is moving to keys.

---

### Open items
- Links for the "Carte suisse des brises", the PNR maps and the Karlis video.
- HR-S&I post-2025 S3 bucket URL.
- The exact RGI 7 file name (needs an Earthdata login).
- The SHP CRS of the IGN CLC18 7z.
- Max zooms marked "~" (swisstopo, EOX), which were not checked.

## AROME historical 10 m wind (NWP baseline)

- **Screening** (days): Open-Meteo historical-forecast API, `models=meteofrance_arome_france`
  (2.5 km; 700 hPa wind, cloud, precip archived from 2024). No key; ~10k location-calls/day.
- **Fields**: Open-Meteo open data on AWS, `https://openmeteo.s3.amazonaws.com/data/meteofrance_arome_france_hd/`
  `wind_{u,v}_component_10m/chunk_<N>.om`, N = hours since 1970 // 108 (`static/meta.json`:
  `chunk_time_length`). Regular 0.01° grid, 37.5–55.4 N × 12 W–16 E (1791 × 2801), south-west
  origin. Layout changed: up to ~2024 `(lat*lon, time)`, 2025+ `(lat, lon, time)`. ~200 MB
  per file; download whole (≈30 s) — remote partial reads via s3fs were orders of magnitude slower.
  Read with `omfiles` (`uv run --group arome`). Values verified cell-for-cell against the API.
