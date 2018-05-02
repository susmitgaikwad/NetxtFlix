import csv
import matplotlib.pyplot as plt
import networkx as nx
from mpldatacursor import datacursor
from networkx.algorithms import bipartite
import itertools
from collections import Counter
import operator

from networkx.algorithms.bipartite import color


class GraphDraw:
    def create(self):
        # Take edgelist input from file
        input_file = open('dataset.csv', encoding='utf8')
        netflix = csv.reader(input_file)

        # Graph Generation
        G = nx.Graph()
        movies = []
        for row in netflix:
            #add movies with name, genre and year released
            G.add_nodes_from([row[3]], genre=row[4], name = row[6], year_released = row[5], bipartite=0)
            movies.append(row[3])
            #add users with genre as User and name as UserID
            G.add_nodes_from([row[0]], genre='User', name = row[0], bipartite=1)
            #add rating and year watched as edge weight
            G.add_edge(row[3], row[0], rating=row[1], year_watched=row[2])

        # Network Characterisation
        d = nx.degree(G)

        name = nx.get_node_attributes(G, 'name')
        movie_nodes = {}
        user_nodes = {}

        # Find out most watched movie and most active user
        for n,d in d:
            if n in movies:
                movie_nodes[n] = d
            else:
                user_nodes[n] = d

        most_watched = max(movie_nodes.values())
        popular = [k for k, v in movie_nodes.items() if v == most_watched]
        print("Most popular movie is", name[popular[0]])
        most_active = max(user_nodes.values())
        active = [k for k, v in user_nodes.items() if v == most_active]
        print("Most active user is", active)

        # Number of edges and nodes in Graph
        total_edges = nx.number_of_edges(G)
        print("Total number of edges in graph are: ", total_edges)
        total_nodes = nx.number_of_nodes(G)
        print("Total number of nodes in graph are: ", total_nodes)

        pos = nx.spring_layout(G)

        movie_names = {}
        # Add movie names to a dictionary for labelling purpose
        for n in G.nodes:
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
            if n not in movies:
                #get all movies watched (neighbors)
                list = G.neighbors(n)
                watched_genres = []
                for g in list:
                    #fetch genre of movie
                    watched_genres.append(genre[g])
                #find most frequent genre for user
                cnt = Counter(watched_genres)
                fav = max(cnt.values())
                fav_genre = sorted(k for k, v in cnt.items() if v == fav)
                fav_genre_list[n] = (''.join(fav_genre))

        nx.set_node_attributes(G, fav_genre_list, 'Favourite Genre')

        favgenre = nx.get_node_attributes(G, 'Favourite Genre')

        edges = G.edges()
        deg = nx.degree(G)
        #nx.draw(G, pos, with_labels=True)


        nx.draw_networkx_labels(G, pos, movie_names, label_pos=0.3)
        #node size determined by how many movies watched and how users have watched that movie i.e Degree of node
        nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=[d * 100 for n,d in deg])
        #Normal edges will have red edges while predicted edges will have different colors

        # nx.draw_networkx_edge_labels(G, pos, font_color='r' ,font_size=5)

        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color='r')

        # Common neighbors
        predicted_edgelist = []

        rating = nx.get_edge_attributes(G, 'rating')
        for n1 in G.nodes:
            for n2 in G.nodes:
                #make sure nodes are not the same and not movie nodes
                if n1 != n2 and n1 not in movies and n2 not in movies:
                    #get common neighbors
                    neighbor = sorted(nx.common_neighbors(G, n1, n2))
                    #set a threshold for how many neighbors should be in common
                    if len(neighbor) > 0 and favgenre[n1]==favgenre[n2]:
                        #predict movie which is excusively a neighbor to second node
                        predicted_movie = [x for x in G.neighbors(n2) if x not in G.neighbors(n1)]
                        i = 0
                        if predicted_movie:
                            #create edgelist of edges predicted using Common-Neighbors
                            new_edge = [n1, predicted_movie[i]]
                            predicted_edgelist.append(new_edge)

        nx.draw_networkx_edges(G, pos, edgelist=predicted_edgelist, edge_color='green', style='dashed')

        # Jaccard's Coefficient
        Jaccards_edgelist = []

        for n1 in G.nodes:
            for n2 in G.nodes:
                # make sure nodes are not the same and not movie nodes
                if n1 != n2 and n1 not in movies and n2 not in movies:
                    #find jaccard's coefficient for a pair of nodes
                    jaccard_index = nx.jaccard_coefficient(G, [(n1, n2)])
                    for u,v,p in jaccard_index:
                        #set threshold for link prediction and check if edge already exists
                        if p >= 0.5 and G.has_edge(u,v)!=True:
                            # predict movie which is excusively a neighbor to second node
                            new_predicted = [x for x in G.neighbors(v) if x not in G.neighbors(u)]
                            i = 0
                            flag = True
                            while new_predicted and flag and i < len(new_predicted):
                                #check if rating of movie to be predicted is greater than 3
                                if int(rating[(v,new_predicted[i])]) >= 3:
                                    new_edge = [u, new_predicted[i]]
                                    Jaccards_edgelist.append(new_edge)
                                    flag = False
                                else:
                                    i+=1

        nx.draw_networkx_edges(G, pos, edgelist=Jaccards_edgelist, edge_color='b', style='dotted')

        plt.show()


d = GraphDraw()
d.create()