#!/usr/bin/env python3
"""
Script Python pour :
- découper population.gpkg par shape_country.gpkg (conserver les géométries qui sont dans ou en partie dans le pays)
- récupérer les centroïdes des entités restantes
- créer un raster "carte de chaleur" en utilisant le champ "nombre" (modèle quadratique, rayon 25 km, pixels 500m)
- créer un buffer de 50 km autour des points de substation
- rasteriser le buffer : 0 = proche de substation (dans le buffer), 1 = hors buffer
- multiplier le raster population par le raster substation
- définir 1 si la valeur de chaleur > 10000, sinon 0

Usage:
    python script_geospatial_population_substation.py \
        --country shape_country.gpkg \
        --population population.gpkg \
        --substations substation.gpkg \
        --out_heatmap heatmap.tif \
        --out_proximity proximity.tif \
        --out_combined combined.tif \
        --out_thresholded thresholded.tif

Dépendances : geopandas, rasterio, shapely, numpy, scipy
Installez-les si nécessaire : pip install geopandas rasterio shapely numpy scipy

Remarques :
- Le script reprojette les données en EPSG:3857 (mètres) pour les opérations métriques.
- Pixel size = 500 m (modifiable). Rayon pour le noyau = 25 000 m (25 km).
- Le modèle quadratique utilisé est : w = nombre * (1 - (d/r)^2) pour d <= r, sinon 0.
"""

import argparse
import math
import warnings

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.transform import from_origin
from rasterio.features import rasterize
from shapely.ops import unary_union
from shapely.geometry import mapping
from scipy.spatial import cKDTree
from shapely.geometry import shape


def main():
    country_shape_file = "../data/CO/osm_brut_country_shape.gpkg"
    population_grid_file = "../data/kontur_population_20231101_r6_3km_centroids.gpkg"
    substation_file = "../data/CO/post_graph_power_nodes_circuit.gpkg"

    pop_heatmap_file = "pop_heatmap.tif"
    pop_heatmap_threshold_file = "pop_heatmap_threshold.tif"
    sub_buffer_file = "sub_buffer.tif"
    out_coverage_file = "out_coverage_brut.tif"
    out_coverage_threshold_file = "out_coverage_threshold.tif"

    pixel_size = 2000.0
    kernel_radius = 25000.0
    metric_crs = "EPSG:3857"

    country = gpd.read_file(country_shape_file).to_crs(metric_crs)
    country_union = unary_union(country.geometry).buffer(kernel_radius+10000)

    if False:
        # Open files
        population = gpd.read_file(population_grid_file).to_crs(metric_crs)
        print(" * Files opened")

        if 'population' not in population.columns:
            raise KeyError("La couche population doit contenir le champ 'population'.")
        print(" * Reprojected layers")

        # découpage
        clipped_pop = clip_population_by_country(population, country_union, metric_crs)
        if clipped_pop.empty:
            warnings.warn("Aucune entité population après découpage par le pays.")

        clipped_pop.to_file("clip_population_CO.gpkg")
        print("Population clipped")

    clipped_pop = gpd.read_file("clip_population_CO.gpkg")
    substations = gpd.read_file(substation_file).to_crs(metric_crs)
    print(" * Files opened (2)")

    # Définir l'étendue raster à la bbox du country (on peut aussi étendre un peu)
    minx, miny, maxx, maxy = country.total_bounds
    # ajouter marge égale au kernel radius pour capturer influence depuis l'extérieur
    margin = kernel_radius
    bounds = (minx - margin, miny - margin, maxx + margin, maxy + margin)
    transform, width, height, xv, yv = make_raster_grid(bounds, pixel_size)

    pop_heatmap = build_heatmap_from_points(clipped_pop, 'population', transform, width, height, xv, yv, kernel_radius)
    pop_heatmap_threshold = (pop_heatmap > 10000.0).astype(np.uint8)
    pop_heatmap_threshold = clip_raster_by_country(pop_heatmap_threshold, transform, country, width, height)
    print(" * Heatmap build")
    # rasterize buffer substations
    proximity = rasterize_substation_buffer(substations, pixel_size, bounds, transform, width, height, buffer_distance=40000.0)

    # save pop_heatmap et proximity
    save_raster(pop_heatmap_file, pop_heatmap, transform, metric_crs, dtype=rasterio.float32, nodata=0)
    save_raster(pop_heatmap_threshold_file, pop_heatmap_threshold, transform, metric_crs, dtype=rasterio.float32, nodata=0)
    save_raster(sub_buffer_file, proximity, transform, metric_crs, dtype=rasterio.uint8, nodata=255)
    print(" * Rasters saved")

    # multiplier
    # proximity est 0 pour proche et 1 pour loin — instruction dit : créer raster 0 si proche, 1 sinon
    combined = pop_heatmap * proximity.astype(np.float32)
    save_raster(out_coverage_file, combined, transform, metric_crs, dtype=rasterio.float32, nodata=0)

    # seuil > 10000 -> 1, else 0
    threshold = (combined > 10000.0).astype(np.uint8)
    threshold = clip_raster_by_country(threshold, transform, country, width, height)
    save_raster(out_coverage_threshold_file, threshold, transform, metric_crs, dtype=rasterio.uint8, nodata=0)

    # vectorisation du raster threshold
    mask = threshold > 0  # True pour les pixels à 1
    features = []
    for geom, val in shapes(threshold, mask=mask, transform=transform):
        features.append({
            "geometry": shape(geom),
            "properties": {"value": int(val)}
        })

    # créer GeoDataFrame
    threshold_gdf = gpd.GeoDataFrame.from_features(features, crs=metric_crs)
    print(" Nb of area = ", len(threshold_gdf))
    threshold_gdf["geometry"] = threshold_gdf["geometry"].buffer(-10000)
    threshold_gdf = threshold_gdf[~threshold_gdf["geometry"].is_empty]
    print(" Nb of area after buffering= ", len(threshold_gdf))
    threshold_gdf["geometry"] = threshold_gdf["geometry"].centroid
    # sauvegarder en GeoPackage
    threshold_gdf.to_file("threshold_vector.gpkg", driver="GPKG")

    print("Traitement terminé. Fichiers générés.")
    print("Computation total > pop = ", pall := pop_heatmap_threshold.sum(axis=(0,1)))
    print("Computation non connected > pop = ", pth := threshold.sum(axis=(0,1)))
    print("pct =",1 - pth/pall)


def clip_population_by_country(pop_gdf, country_union, crs):
    # Intersecter pour garder uniquement les parties à l'intérieur du pays (ou en partie)
    # On suppose qu'il y a au moins une géométrie pays ; si plusieurs, on les unionne

    country_single = gpd.GeoDataFrame(geometry=[country_union], crs=crs)
    clipped = pop_gdf.sjoin(country_single, how="inner")
    return clipped


def compute_centroids(gdf):
    # Assumer gdf en CRS métrique
    cent = gdf.copy()
    cent["centroid"] = cent.geometry.centroid
    cent = cent.set_geometry("centroid")
    return cent


def make_raster_grid(bounds, pixel_size):
    """Retourne transform, width, height et arrays x_centers,y_centers (2D)
    bounds = (minx, miny, maxx, maxy)
    """
    minx, miny, maxx, maxy = bounds
    width = math.ceil((maxx - minx) / pixel_size)
    height = math.ceil((maxy - miny) / pixel_size)
    # ajuster l'origin pour coller aux pixels
    transform = from_origin(minx, maxy, pixel_size, pixel_size)
    # centres des pixels
    xs = minx + (np.arange(width) + 0.5) * pixel_size
    ys = maxy - (np.arange(height) + 0.5) * pixel_size
    xv, yv = np.meshgrid(xs, ys)
    return transform, width, height, xv, yv


def clip_raster_by_country(raster_array, transform, country_gdf, width, height):
    # créer masque rasterisé du pays
    country_union = unary_union(country_gdf.geometry)
    shapes = [(mapping(country_union), 1)]
    mask = rasterize(shapes, out_shape=(height, width), transform=transform, fill=0, dtype=np.uint8)
    return raster_array * mask


def build_heatmap_from_points(centroids_gdf, value_field, transform, width, height, xv, yv, kernel_radius):
    """Construit la heatmap (float32) en utilisant le noyau quadratique pondéré par value_field.
    - centroids_gdf : GeoDataFrame en CRS métrique et géométrie en points
    - xv,yv : matrices 2D des coordonnées des centres de pixels
    """
    # flatten grid centers
    grid_points = np.column_stack((xv.ravel(), yv.ravel()))  # (Ncells, 2)
    tree = cKDTree(grid_points)

    heat = np.zeros(grid_points.shape[0], dtype=np.float64)

    nombres = centroids_gdf[value_field].fillna(0).values
    pts = np.array([[p.x, p.y] for p in centroids_gdf.geometry])

    r = float(kernel_radius)

    for (px, py), nb in zip(pts, nombres):
        if nb == 0:
            continue
        # find grid indices within radius
        idxs = tree.query_ball_point([px, py], r)
        if not idxs:
            continue
        cell_coords = grid_points[idxs]
        dists = np.sqrt((cell_coords[:, 0] - px) ** 2 + (cell_coords[:, 1] - py) ** 2)
        # modèle quadratique : w = nb * (1 - (d/r)^2) pour d <= r
        weights = nb * (1.0 - (dists / r) ** 2)
        # contributions
        heat[idxs] += weights

    heatmap = heat.reshape((height, width))
    return heatmap.astype(np.float32)


def rasterize_substation_buffer(substations_gdf, pixel_size, bounds, transform, width, height, buffer_distance):
    # buffer_distance en mètres (50 km = 50000 m)
    # create buffers in metric CRS
    buffers = substations_gdf.geometry.buffer(buffer_distance)
    # fusionner et dissoudre
    if len(buffers) == 0:
        merged = None
    else:
        merged = unary_union(buffers)
    # rasterize : fill=1 partout sauf brûler 0 pour le buffer
    if merged is None or merged.is_empty:
        # no buffers: all ones
        arr = np.ones((height, width), dtype=np.uint8)
    else:
        shapes = [ (mapping(merged), 0) ]
        arr = rasterize(
            shapes,
            out_shape=(height, width),
            transform=transform,
            fill=1,
            dtype=np.uint8,
        )
    return arr


def save_raster(path, array, transform, crs, dtype=rasterio.float32, nodata=None):
    height, width = array.shape
    with rasterio.open(
        path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=dtype,
        crs=crs,
        transform=transform,
        nodata=nodata,
        compress='lzw'
    ) as dst:
        dst.write(array.astype(dtype), 1)





if __name__ == '__main__':
    main()
