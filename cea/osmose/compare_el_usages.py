from __future__ import division
import numpy as np
import pandas as pd
import os
import operator
import matplotlib.pyplot as plt


def main(building, building_result_path):
    # get paths to chiller_T_tech_df and el csv
    paths = path_to_elec_csv_files(building_result_path)
    chiller_paths = path_to_chiller_csv_files(building_result_path)

    el_dfs = {}
    cop_mean = {}
    compare_df = pd.DataFrame()
    for path in paths:
        file_name = path.split('\\')
        tech = [x for x in file_name if 'HCS' in x][0].split('_')[2]
        el_dfs[tech] = pd.read_csv(path)
        index = el_dfs[tech].shape[0] - 1
        cop_mean[tech] = el_dfs[tech]['cop_system'].replace(0, np.nan).mean()
        compare_df[tech] = el_dfs[tech].ix[index][1:]
    compare_df.to_csv(path_to_save_compare_df(building, building_result_path))

    # get chiller_T_tech_df df from all tech
    chiller_T_all_tech_df = get_chiller_T_from_all_techs(chiller_paths)
    plot_chiller_temperatures_bar(chiller_T_all_tech_df, building, building_result_path)
    plot_chiller_temperatures_scatter(chiller_T_all_tech_df, building, building_result_path)


    return


def get_chiller_T_from_all_techs(chiller_paths):
    i = 0
    for path in chiller_paths:
        if i == 0:
            chiller_T_all_tech_df = pd.read_csv(path)
            chiller_T_all_tech_df = chiller_T_all_tech_df.set_index(chiller_T_all_tech_df.columns[0])
            i = i + 1
        else:
            chiller_T_tech_df = pd.read_csv(path)
            chiller_T_tech_df = chiller_T_tech_df.set_index(chiller_T_tech_df.columns[0])
            chiller_T_all_tech_df = chiller_T_all_tech_df.append(chiller_T_tech_df)
    float_columns = [float(x) for x in chiller_T_all_tech_df.columns]
    float_columns.sort()
    string_columns = [str(x) for x in float_columns]
    chiller_T_all_tech_df = chiller_T_all_tech_df.reindex(string_columns, axis=1)
    chiller_T_all_tech_df = chiller_T_all_tech_df.fillna(0)
    return chiller_T_all_tech_df


def plot_chiller_temperatures_bar(chiller_df, building, building_result_path):
    X = np.arange(chiller_df.columns.size)
    fig, ax = plt.subplots()
    width = 0.00
    # colors = {'HCS_3for2': '#C97A64', 'HCS_coil': '#4E9DA3', 'HCS_ER0': '#E2BB56', 'HCS_IEHX': '#889164'}
    colors = {'HCS_3for2': '#C96A50', 'HCS_coil': '#3E9AA3', 'HCS_ER0': '#E2B43F', 'HCS_IEHX': '#51443D'}
    for i in range(chiller_df.index.size):
        color = colors[chiller_df.index[i]]
        ax.bar(X + width, chiller_df.loc[chiller_df.index[i]][:], width=0.15, label=chiller_df.index[i], color=color)
        width = width + 0.15
    # ax.bar(X + 0.25, chiller_df.loc[chiller_df.index[1]][:], width=0.25, label=chiller_df.index[1])
    ax.legend(loc='upper right')
    ax.set_xticks(X + width / 2)
    ax.set_xticklabels(tuple(chiller_df.columns))
    # ax.set_xticks(chiller_df.columns)
    ax.set(xlabel='Temperature [C]', ylabel='Frequency [%]', ylim=(0, 100))
    # plt.show()
    fig.savefig(path_to_save_chiller_t(building, building_result_path))
    return np.nan


def plot_chiller_temperatures_scatter(chiller_df, building, building_result_path):
    chiller_dict = chiller_df.T.to_dict()

    # sort two level dict with the value of key in second level
    sorted_dict = sort_dict_with_second_level_key(chiller_dict)

    # x axis (keys of the first level dict)
    x_labels = list(chiller_dict.keys())
    x_values = list(range(len(x_labels)))
    # lookup table mapping category
    lookup_table = dict((v, k) for k, v in enumerate(x_labels))
    # build a list of points (x,y,annotation)
    points = [(lookup_table[action], key, anno)
              for action, values in chiller_dict.items()
              for key, anno in (values if values else {}).items()]
    x, y, anno = zip(*points)
    y_float = tuple(map(lambda i: float(i), y))
    # y axis (keys of the second level dict)
    y_values = [float(i) for i in chiller_df.columns]
    y_labels = [str(v) for v in y_values]
    # marker size
    area = tuple(map(lambda x: 10 * (x), anno))

    # format the plt
    plt.figure()
    plt.title(building)
    # plt.xlabel('x')
    plt.ylabel('Chilled water temperature [C]')
    plt.xticks(x_values, x_labels)
    plt.yticks(y_values, y_labels)
    plt.axis([min(x_values) - 0.5, max(x_values) + 0.5,
              min(y_values) - 0.5, max(y_values) + 0.5])
    plt.scatter(x, y_float, s=area)
    # plt.show()
    plt.savefig(path_to_save_chw_scatter(building, building_result_path))
    return np.nan


def sort_dict_with_second_level_key(two_level_dict):
    dict_sorted_with_second_level_key = {}
    for k, v in two_level_dict.items():
        new_sub_dict = {}
        for i, j in v.items():
            new_sub_dict[float(i)] = j
        new_sub_dict_sorted = sorted(new_sub_dict.items(), key=operator.itemgetter(0))
        dict_sorted_with_second_level_key[k] = new_sub_dict_sorted
    return dict_sorted_with_second_level_key


def path_to_elec_csv_files(building_result_path):
    """
    find files with _el.csv and return a list of paths
    :param building:
    :return:
    """
    # path_to_folder = PATH_TO_FOLDER + building
    all_files_in_path = os.listdir(building_result_path)
    path_to_files = []
    file_name = 'el.csv'
    for file in all_files_in_path:
        if file_name in file:
            path_to_file = os.path.join(building_result_path, file)
            path_to_files.append(path_to_file)
    return path_to_files


def path_to_chiller_csv_files(building_result_path):
    """
    find files with _el.csv and return a list of paths
    :param building:
    :return:
    """
    # path_to_folder = PATH_TO_FOLDER + building
    all_files_in_path = os.listdir(building_result_path)
    path_to_files = []
    file_name = 'chiller.csv'
    for file in all_files_in_path:
        if file_name in file:
            path_to_file = os.path.join(building_result_path, file)
            path_to_files.append(path_to_file)
    return path_to_files


def path_to_save_compare_df(building, building_result_path):
    filename = building + '_el_compare.csv'
    path_to_file = os.path.join(building_result_path, filename)
    return path_to_file


def path_to_save_chiller_t(building, building_result_path):
    filename = building + '_chiller.png'
    path_to_file = os.path.join(building_result_path, filename)
    return path_to_file

def path_to_save_chw_scatter(building, building_result_path):
    filename = building + '_chw_scatter.png'
    path_to_file = os.path.join(building_result_path, filename)
    return path_to_file


if __name__ == '__main__':
    building = "B001"
    building_result_path = 'C:\\Users\\Shanshan\\Documents\\WP1_results\\WTP_CBD_m_WP1_RET\\B001_168'
    main(building, building_result_path)