# Libraries
from matplotlib import pyplot as plt
from math import pi

#this function was adapted from code posted by Yan Holtz, here
#https://python-graph-gallery.com/390-basic-radar-chart/
def plotModel(input_df, group_list, group_key, nTopics,plot_legend=True, savename=""):
    '''
    This function plots the average topic contribution for group elements of a dataframes. Entries can be groupoed according to a group key passed to the function

    :param input_df: the data frame
    :param group_list: The list of groups to plot in the spider plot. Needs to be a valid entry in the column specified in the next parameters
    :param group_key: The key for the column from which the groups should be elected, for example a cluster_id column, or the category column
    :param nTopics: Numer of topics used for clustering
    :param plot_legend: Set to false if the legend obscures the plot
    :param savename: give a filename to automatically save a PNG plot to disk
    :return:
    '''
    #figure out the maximumal topic key
    max_topic_key = 'topic_' + str(nTopics - 1)
    temp_df = input_df.loc[:, 'topic_0':max_topic_key].convert_objects()
    temp_df[group_key] = input_df[group_key].convert_objects(convert_numeric=True)
    cols = temp_df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    temp_df = temp_df[cols]
    #calculate the average topic contribution for each group.
    df = temp_df.groupby(group_key).mean().reset_index()

    categories = list(df)[1:]
    N = len(categories)


    cluster_values = {}
    for r in range(0, df.shape[0]):
        cluster_id = df.loc[r][group_key]
        if cluster_id in group_list:
            values = df.loc[r].drop(group_key).values.flatten().tolist()
            values += values[:1]
            cluster_values[cluster_id] = values

    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    # Initialise the spider plot
    ax = plt.subplot(111, polar=True)

    # Draw one axe per variable + add labels labels yet
    plt.xticks(angles[:-1], categories, color='grey', size=18)

    # Draw ylabels
    ax.set_rlabel_position(0)
    plt.yticks([0.20, 0.40, 0.60, 0.80, 1.0], ["0.2", "0.4", "0.6", "0.8", "1.0"], color="grey", size=15)
    plt.ylim(0, 1.0)

    for cluster in group_list:
        values = cluster_values[cluster]
        # Plot data
        ax.plot(angles, values, linewidth=1, linestyle='solid', label=cluster)
        ax.fill(angles, values, alpha=0.1)
    if plot_legend:
        plt.legend(loc=(1, 0.8))
    if savename:
        plt.savefig(savename)