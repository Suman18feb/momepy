#!/usr/bin/env python
# -*- coding: utf-8 -*-

# intensity.py
# definitons of intensity characters

from tqdm import tqdm  # progress bar
import pandas as pd


def radius(gpd_df, cpt, radius):
    """
    Get a list of indices of objects within radius.

    Parameters
    ----------
    gpd_df : GeoDataFrame
        GeoDataFrame containing point objects to analyse
    cpt : shapely.Point
        shapely point representing the center of radius
    radius : float
        radius

    Returns
    -------
    list
        Return only the neighbour indices, sorted by distance in ascending order

    Notes
    ---------
    https://stackoverflow.com/questions/44622233/rtree-count-points-in-the-neighbourhoods-within-each-point-of-another-set-of-po

    """
    # Spatial index
    sindex = gpd_df.sindex
    # Bounding box of rtree search (West, South, East, North)
    bbox = (cpt.x - radius, cpt.y - radius, cpt.x + radius, cpt.y + radius)
    # Potential neighbours
    good = []
    for n in sindex.intersection(bbox):
        dist = cpt.distance(gpd_df['geometry'].iloc[n])
        if dist < radius:
            good.append((dist, n))
    # Sort list in ascending order by `dist`, then `n`
    good.sort()
    # Return only the neighbour indices, sorted by distance in ascending order
    return [x[1] for x in good]


def frequency(objects, look_for, id_column='uID', rad=400):
    """
    Calculate frequency (count) of objects in a given radius.

    .. math::
        count

    Parameters
    ----------
    objects : GeoDataFrame
        GeoDataFrame containing objects to analyse
    look_for : GeoDataFrame
        GeoDataFrame with measured objects (could be the same as objects)
    id_column : str
        name of the column with unique id

    Returns
    -------
    Series
        Series containing resulting values.

    References
    ---------

    """

    print('Calculating frequency...')

    objects_centroids = objects.copy()
    objects_centroids['geometry'] = objects_centroids.centroid

    look_for_centroids = look_for.copy()
    look_for_centroids['geometry'] = look_for_centroids.centroid

    # define empty list for results
    results_list = []

    for index, row in tqdm(objects_centroids.iterrows(), total=objects_centroids.shape[0]):
        neighbours = radius(look_for_centroids, row['geometry'], rad)
        results_list.append(len(neighbours))

    series = pd.Series(results_list)

    print('Frequency calculated.')
    return series


def covered_area_ratio(objects, look_for, area_column, look_for_area_column, id_column="uID"):
    """
    Calculate covered area ratio of objects.

    .. math::
        \\textit{covering object area} \over \\textit{covered object area}

    Parameters
    ----------
    objects : GeoDataFrame
        GeoDataFrame containing objects being covered (e.g. land unit)
    look_for : GeoDataFrame
        GeoDataFrame with covering objects (e.g. building)
    area_column : str
        name of the column of objects gdf where is stored area value
    look_for_area_column : str
        name of the column of look_for gdf where is stored area value
    id_column : str
        name of the column with unique id. If there is none, it could be generated by unique_id().

    Returns
    -------
    Series
        Series containing resulting values.

    References
    ---------

    """
    print('Calculating covered area ratio...')

    print('Merging DataFrames...')
    look_for = look_for[[id_column, look_for_area_column]]  # keeping only necessary columns
    look_for.rename(index=str, columns={look_for_area_column: 'lf_area'}, inplace=True)
    objects_merged = objects.merge(look_for, on=id_column)  # merging dataframes together

    print('Calculating CAR...')

    # define empty list for results
    results_list = []

    # fill new column with the value of area, iterating over rows one by one
    for index, row in tqdm(objects_merged.iterrows(), total=objects_merged.shape[0]):
            results_list.append(row['lf_area'] / row[area_column])

    series = pd.Series(results_list)

    print('Covered area ratio calculated.')
    return series


def floor_area_ratio(objects, look_for, area_column, look_for_area_column, id_column="uID"):
    """
    Calculate floor area ratio of objects.

    .. math::
        \\textit{covering object floor area} \over \\textit{covered object area}

    Parameters
    ----------
    objects : GeoDataFrame
        GeoDataFrame containing objects being covered (e.g. land unit)
    look_for : GeoDataFrame
        GeoDataFrame with covering objects (e.g. building)
    area_column : str
        name of the column of objects gdf where is stored area value
    look_for_area_column : str
        name of the column of look_for gdf where is stored floor area value
    id_column : str
        name of the column with unique id. If there is none, it could be generated by unique_id().

    Returns
    -------
    Series
        Series containing resulting values.

    References
    ---------

    """
    print('Calculating floor area ratio...')

    print('Merging DataFrames...')
    look_for = look_for[[id_column, look_for_area_column]]  # keeping only necessary columns
    look_for.rename(index=str, columns={look_for_area_column: 'lf_area'}, inplace=True)
    objects_merged = objects.merge(look_for, on=id_column)  # merging dataframes together

    print('Calculating FAR...')

    # define empty list for results
    results_list = []

    # fill new column with the value of area, iterating over rows one by one
    for index, row in tqdm(objects_merged.iterrows(), total=objects_merged.shape[0]):
        results_list.append(row['lf_area'] / row[area_column])

    series = pd.Series(results_list)

    print('Floor area ratio calculated.')
    return series


def elements_in_block(blocks, elements, left_id, right_id, weighted=False):
    """
    Calculate the number of elements within block.

    If weighted=True, number of elements will be divided by the area of block, to return relative value.

    .. math::
        \\sum_{i \\in block} (n_i);\\space \\frac{\\sum_{i \\in block} (n_i)}{area_{block}}

    Parameters
    ----------
    blocks : GeoDataFrame
        GeoDataFrame containing blocks to analyse
    buildings : GeoDataFrame
        GeoDataFrame containing buildings to analyse
    left_id : str
        name of the column where is stored block ID in blocks gdf
    right_id : str
        name of the column where is stored block ID in elements gdf
    weighted : bool (default False)
        if weighted=True, number of buildings will be divided by the area of block, to return relative value.

    Returns
    -------
    Series
        Series containing resulting values.

    References
    ---------
    Hermosilla T, Ruiz LA, Recio JA, et al. (2012) Assessing contextual descriptive features
    for plot-based classification of urban areas. Landscape and Urban Planning, Elsevier B.V.
    106(1): 124–137.
    Feliciotti A (2018) RESILIENCE AND URBAN DESIGN:A SYSTEMS APPROACH TO THE
    STUDY OF RESILIENCE IN URBAN FORM. LEARNING FROM THE CASE OF GORBALS. Glasgow.
    """
    count = collections.Counter(elements[right_id])

    results_list = []
    for index, row in tqdm(blocks.iterrows(), total=blocks.shape[0]):
        if weighted is True:
            results_list.append(count[row[left_id]] / row.geometry.area)
        else:
            results_list.append(count[row[left_id]])

    series = pd.Series(results_list)

    return series


def courtyards(objects, block_id, weights_matrix=None):
    """
    Calculate the number of courtyards within the joined structure.

    Parameters
    ----------
    objects : GeoDataFrame
        GeoDataFrame containing objects to analyse
    block_id : str
        name of the column where is stored block ID
    weights_matrix : libpysal.weights, optional
        spatial weights matrix - If None, Queen contiguity matrix will be calculated
        based on objects. It is to denote adjacent buildings.

    Returns
    -------
    Series
        Series containing resulting values.

    Notes
    -----
    Script is not optimised at all, so it is currently extremely slow.
    """
    # define empty list for results
    results_list = []

    print('Calculating courtyards...')

    if not all(objects.index == range(len(objects))):
        raise ValueError('Index is not consecutive range 0:x, spatial weights will not match objects.')

    # if weights matrix is not passed, generate it from objects
    if weights_matrix is None:
        print('Calculating spatial weights...')
        from libpysal.weights import Queen
        weights_matrix = Queen.from_dataframe(objects, silence_warnings=True)
        print('Spatial weights ready...')

    # dict to store nr of courtyards for each uID
    courtyards = {}

    for index, row in tqdm(objects.iterrows(), total=objects.shape[0]):
        # if the id is already present in courtyards, continue (avoid repetition)
        if index in courtyards:
            continue
        else:
            to_join = [index]  # list of indices which should be joined together
            neighbours = []  # list of neighbours
            weights = weights_matrix.neighbors[index]  # neighbours from spatial weights
            for w in weights:
                neighbours.append(w)  # make a list from weigths

            for n in neighbours:
                while n not in to_join:  # until there is some neighbour which is not in to_join
                    to_join.append(n)
                    weights = weights_matrix.neighbors[n]
                    for w in weights:
                        neighbours.append(w)  # extend neighbours by neighbours of neighbours :)
            joined = objects.iloc[to_join]
            dissolved = joined.geometry.buffer(0.01).unary_union  # buffer to avoid multipolygons where buildings touch by corners only
            try:
                interiors = len(list(dissolved.interiors))
            except(ValueError):
                print('Something happened.')
            for b in to_join:
                courtyards[b] = interiors  # fill dict with values
    # copy values from dict to gdf
    for index, row in tqdm(objects.iterrows(), total=objects.shape[0]):
        results_list.append(courtyards[index])

    series = pd.Series(results_list)
    print('Courtyards calculated.')
    return series


def gross_density(objects, buildings, area, character, weights_matrix=None, order=3, unique_id='uID'):
    """
    Calculate the density

    .. math::


    Parameters
    ----------
    objects : GeoDataFrame
        GeoDataFrame containing tessellation objects to analyse
    buildings : GeoDataFrame
        GeoDataFrame containing buildings
    area : str
        name of the column with area values
    character : str
        name of the column with values of target character for density calculation
    weights_matrix : libpysal.weights, optional
        spatial weights matrix - If None, Queen contiguity matrix of selected order will be calculated
        based on objects.
    order : int
        order of Queen contiguity
    unique_id : str
        name of the column with unique id. If there is none, it could be generated by unique_id()

    Returns
    -------
    Series
        Series containing resulting values.

    References
    ---------
    Jacob??
    """
    # define empty list for results
    results_list = []

    print('Calculating gross density...')

    if not all(objects.index == range(len(objects))):
        raise ValueError('Index is not consecutive range 0:x, spatial weights will not match objects.')

    if weights_matrix is None:
        print('Generating weights matrix (Queen) of {} topological steps...'.format(order))
        from momepy import Queen_higher
        # matrix to define area of analysis (more steps)
        weights_matrix = Queen_higher(objects, k=order)

    # iterating over rows one by one
    for index, row in tqdm(objects.iterrows(), total=objects.shape[0]):
        neighbours_id = weights_matrix.neighbors[index]
        neighbours_id.append(index)
        neighbours = objects.iloc[neighbours_id]

        fa = buildings.loc[buildings[unique_id].isin(neighbours[unique_id])][character]
        results_list.append(sum(fa) / sum(neighbours[area]))

    series = pd.Series(results_list)
    print('Gross density calculated.')
    return series


def blocks_count(tessellation, block_id, spatial_weights=None, order=5):
    """
    Calculates the weighted number of blocks

    Number of blocks within `k` topological steps defined in spatial_weights weighted by the analysed area.

    .. math::
        \\frac{\\sum_{i=1}^{n} {blocks}}{\\sum_{i=1}^{n} area_{i}}
        NOT SURE

    Parameters
    ----------
    tessellation : GeoDataFrame
        GeoDataFrame containing morphological tessellation
    block_id : str, list, np.array, pd.Series (default None)
        the name of the objects dataframe column, np.array, or pd.Series where is stored block ID.
    spatial_weights : libpysal.weights (default None)
        spatial weights matrix - If None, Queen contiguity matrix of set order will be calculated
        based on objects.
    order : int (default 5)
        order of Queen contiguity. Used only when spatial_weights=None.


    Returns
    -------
    Series
        Series containing resulting values.

    References
    ----------
    Jacob

    Examples
    --------

    """
    # define empty list for results
    results_list = []

    if not isinstance(block_id, str):
        block_id['mm_bid'] = block_id
        block_id = 'mm_bid'

    if not all(tessellation.index == range(len(tessellation))):
        raise ValueError('Index is not consecutive range 0:x, spatial weights will not match objects.')

    if spatial_weights is None:
        print('Generating weights matrix (Queen) of {} topological steps...'.format(order))
        from momepy import Queen_higher
        # matrix to define area of analysis (more steps)
        spatial_weights = Queen_higher(tessellation, k=order)

    print('Calculating blocks...')

    for index, row in tqdm(tessellation.iterrows(), total=tessellation.shape[0]):
        neighbours = spatial_weights.neighbors[index]
        neighbours.append(index)
        vicinity = tessellation.iloc[neighbours]

        results_list.append(len(set(list(vicinity[block_id]))) / sum(vicinity.geometry.area))

    series = pd.Series(results_list)

    if 'mm_bid' in tessellation.columns:
        tessellation.drop(columns=['mm_bid'], inplace=True)

    print('Blocks calculated.')
    return series

# objects.to_file("/Users/martin/Strathcloud/Personal Folders/Test data/Prague/p7_voro_single4.shp")
#
# objects = gpd.read_file("/Users/martin/Strathcloud/Personal Folders/Test data/Prague/p7_voro_single.shp")
# column_name = 'test'
# objects
# objects2.head
# objects['geometry'] = objects.centroid
# objects_centroids
