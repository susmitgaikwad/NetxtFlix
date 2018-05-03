import csv
from builtins import list

import matplotlib.pyplot as plt
import networkx as nx
from mpldatacursor import datacursor
from networkx.algorithms import bipartite
import itertools
from collections import Counter
import numpy as np
import operator

from networkx.algorithms.bipartite import color


class GraphDraw:
    def create(self):
        # Take edgelist input from file
        input_file = open('1000_dataset.csv', encoding='utf8')
        netflix = csv.reader(input_file)

        # Graph Generation
        G = nx.Graph()
        movies = []
        for row in netflix:
            #add movies with name, genre and year released
            G.add_nodes_from([row[3]], genre=row[4], name = row[6], year_released = row[5], bipartite=0)
            if row[3] not in movies:
                movies.append(row[3])
            #add users with genre as User and name as UserID
            G.add_nodes_from([row[0]], genre='User', name = row[0], bipartite=1)
            #add rating and year watched as edge weight
            G.add_edge(row[3], row[0], rating=row[1], year_watched=row[2])

        # Network Characterisation
        d = nx.degree(G)

        bi = nx.get_node_attributes(G, 'bipartite')

        name = nx.get_node_attributes(G, 'name')
        movie_nodes = {}
        user_nodes = {}

        # Find out most watched movie and most active user
        for n,d in d:
            if bi[n]==0:
                movie_nodes[n] = d
            else:
                user_nodes[n] = d

        c = Counter(movie_nodes)
        mc_movies = c.most_common(10)

        c_u = Counter(user_nodes)
        mc_users = c_u.most_common(10)


        # plt.bar(range(len(mc_movies)), mc_movies.values(), align='center')
        # plt.xticks(range(len(mc_movies)), mc_movies.keys())
        # plt.show()
        print(mc_movies)
        print(mc_users)

        most_watched = max(movie_nodes.values())
        popular = [k for k, v in movie_nodes.items() if v == most_watched]
        print('Most popular movie is ', name[popular[0]],' with view count = ',most_watched)
        most_active = max(user_nodes.values())
        active = [k for k, v in user_nodes.items() if v == most_active]
        print("Most active user is", active, ' with number of movies watched = ', most_active)

        # Number of edges and nodes in Graph
        total_edges = nx.number_of_edges(G)
        print("Total number of edges in graph are: ", total_edges)
        total_nodes = nx.number_of_nodes(G)
        print("Total number of nodes in graph are: ", total_nodes)
        print('Number of movie nodes are: ', len(movies))
        print('Number of user nodes are: ', total_nodes-len(movies))

        pos = nx.spring_layout(G)

        movie_names = {}
        # Add movie names to a dictionary for labelling purpose
        for n in movie_nodes:
            movie_names[n] = G.node[n]['name']

        # Use genre to create a mapping between color and genre, for genre based color coding
        genre = nx.get_node_attributes(G, 'genre')
        genres = set(genre.values())
        mapping = dict(zip(sorted(genres), itertools.count()))
        colors = [mapping[G.node[n]['genre']] for n in G.nodes]

        # Favourite Genre of user
        fav_genre_list = {}
        for n in G.nodes:
            #find favourite genre for user node
            if bi[n]==1:
                #get all movies watched (neighbors)
                list_neighbors = G.neighbors(n)
                watched_genres = []
                for g in list_neighbors:
                    #fetch genre of movie
                    watched_genres.append(genre[g])
                #find most frequent genre for user
                cnt = Counter(watched_genres)
                fav = max(cnt.values())
                fav_genre = sorted(k for k, v in cnt.items() if v == fav)
                fav_genre_list[n] = (''.join(fav_genre))

        nx.set_node_attributes(G, fav_genre_list, 'Favourite Genre')

        favgenre = nx.get_node_attributes(G, 'Favourite Genre')

        #Most common favgenres
        c_g = Counter(fav_genre_list.values())
        mc_genres = c_g.most_common(10)
        print(mc_genres)
        # mc_genres.sort(key=lambda x: x[1], reverse=True)
        #
        # # save the names and their respective count separately
        # # reverse the tuples to go from most common to least common genre
        # fgenre = list(zip(*mc_genres))[0]
        # number = list(zip(*mc_genres))[1]
        # x_pos = np.arange(len(fgenre))

        # plt.bar(x_pos, number, align='center')
        # plt.xticks(x_pos, fgenre)
        # plt.xlabel('Top 10 Common Favourite Genres')
        # plt.ylabel('Popularity of Genre')
        # plt.show()

        edges = G.edges()
        deg = nx.degree(G)
        #nx.draw(G, pos, with_labels=True)


        #nx.draw_networkx_labels(G, pos, movie_names, label_pos=0.3)
        #node size determined by how many movies watched and how users have watched that movie i.e Degree of node
        nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=[d * 10 for n,d in deg])
        #Normal edges will have red edges while predicted edges will have different colors

        # nx.draw_networkx_edge_labels(G, pos, font_color='r' ,font_size=5)

        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color='r', width=0.5)

        # Common neighbors
        predicted_edgelist = []

        rating = nx.get_edge_attributes(G, 'rating')
        for n1 in G.nodes:
            for n2 in G.nodes:
                #make sure nodes are not the same and not movie nodes
                if n1 != n2 and bi[n1]==1 and bi[n2]==1:
                    #get common neighbors
                    neighbor = sorted(nx.common_neighbors(G, n1, n2))
                    #set a threshold for how many neighbors should be in common
                    if len(neighbor) > 1 and favgenre[n1]==favgenre[n2]:
                        #predict movie which is excusively a neighbor to second node
                        predicted_movie = [x for x in G.neighbors(n2) if x not in G.neighbors(n1)]
                        i = 0
                        if predicted_movie:
                            #create edgelist of edges predicted using Common-Neighbors
                            new_edge = [n1, predicted_movie[i]]
                            predicted_edgelist.append(new_edge)
        print(predicted_edgelist)
        nx.draw_networkx_edges(G, pos, edgelist=predicted_edgelist, edge_color='green', width=3.0)

        # Jaccard's Coefficient
        Jaccards_edgelist = []

        for n1 in G.nodes:
            for n2 in G.nodes:
                # make sure nodes are not the same and not movie nodes
                if n1 != n2 and bi[n1]==1 and bi[n2]==1:
                    #find jaccard's coefficient for a pair of nodes
                    jaccard_index = nx.jaccard_coefficient(G, [(n1, n2)])
                    for u,v,p in jaccard_index:
                        #set threshold for link prediction and check if edge already exists
                        if p >= 0.5:
                            # predict movie which is excusively a neighbor to second node
                            new_predicted = [x for x in G.neighbors(v) if x not in G.neighbors(u)]
                            i = 0
                            #set flag to come out of loop once movie is recommended
                            flag = True

                            # make sure that the unique list of unseen movies is not empty or that we don't iterate beyond the index
                            while i < len(new_predicted) and len(new_predicted) !=0 and flag:
                                new_movie = new_predicted[i]
                                #check if rating of movie to be predicted is greater than 3
                                if G.has_edge(u, new_movie) != True and G.has_edge(v, new_movie):

                                    user_rating = G[v][new_movie]['rating']

                                    if int(user_rating) > 3:
                                        new_edge = [u, new_predicted[i]]
                                        Jaccards_edgelist.append(new_edge)
                                        flag = False
                                    else:
                                        i+=1

        print(Jaccards_edgelist)
        nx.draw_networkx_edges(G, pos, edgelist=Jaccards_edgelist, edge_color='b', width=3.0)

        plt.show()


d = GraphDraw()
d.create()
