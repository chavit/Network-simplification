import networkx as nx
import random
import sys
import numpy as np
from datetime import datetime,time,date,timedelta


# routine

DEST_INT = 100000
LARGE_INT = 1000000
BIG_CAP = 10000000

def my_print(s):
    print "[" + str(datetime.now()) + "] " + s

def cap(G, e):
	return G[e[0]][e[1]]['capacity']

def full_cap(G):
	return np.sum([G[u][v]['capacity'] for u,v in G.edges_iter() if u>=0 and v<DEST_INT])

def full_cap_multi(G):
	return np.sum([d['capacity'] for u,v,k,d in G.edges_iter(keys=True,data=True) if u>=0 and v<DEST_INT])

def full_cap_all(G):
	return np.sum([G[u][v]['capacity'] for u,v in G.edges_iter()])

def full_cap_multi_all(G):
	return np.sum([d['capacity'] for u,v,k,d in G.edges_iter(keys=True,data=True)])

def num_nodes(G):
	return len([n for n in G.nodes() if n>=0 and n<DEST_INT])

def num_edges(G):
	return len([(u,v) for (u,v) in G.edges() if u>=0 and v<DEST_INT])


def read_graph(in_fname):
	Gfull=nx.DiGraph(nodetype=int)
	with open(in_fname) as f:
		for line in f:
			arr = line.strip().split()
			if len(arr) == 3:
				src,dst,wei = int(arr[0]), int(arr[1]), int(arr[2])
				if src < 0 or dst >= DEST_INT:
					wei = BIG_CAP
				Gfull.add_edge(src, dst, capacity=wei, weight=1)


	recheableforward = set([])
	recheablebackward = set([])

	for u in Gfull.nodes():
		if u < 0:
			recheableforward = recheableforward.union(nx.descendants(Gfull, u))
		if (u >= DEST_INT):
			recheablebackward = recheablebackward.union(nx.ancestors(Gfull, u))

	recheable = recheableforward.intersection(recheablebackward)
	for u in Gfull.nodes():
		if u >= 0 and u < DEST_INT and recheable.isdisjoint([u]):
			Gfull.remove_node(u)

	return Gfull


def validate_topology(G):
	for u in G.nodes():
		succ = [x for x in G.successors(u) if x >= DEST_INT]
		prec = [x for x in G.predecessors(u) if x < 0]
		if len(succ) > 0 and len(prec) > 0:
			return False
	return True


def convert_to_multi(G_input):
	G = nx.MultiDiGraph()
	G.add_nodes_from(G_input.nodes())
	G.add_edges_from([ (u, v, G_input[u][v]) for u,v in G_input.edges_iter() ])
	return G


def convert_to_di(G_input):
	G=nx.DiGraph(nodetype=int)
	G.add_nodes_from(G_input.nodes())
	for u,v,k,dd in G_input.edges_iter(keys=True, data=True):
		if u != v:
			if (G.has_edge(u,v) == False):
				G.add_edge(u,v,dd)
			else:
				G[u][v]['capacity'] = G[u][v]['capacity'] + dd['capacity']
	return G


#minimizing bandwidth

def calculate_input_potential(Ginput, v):
	G = Ginput.copy()
	G.add_node(-LARGE_INT)

	for n in G.nodes():
		if n < 0:
			G.add_edge(-LARGE_INT, n, capacity=BIG_CAP, weight=1)

	flowValue, _ = nx.maximum_flow(G, -LARGE_INT, v)
	return flowValue

def estimate_input_potential(G, v):
	return np.sum([ cap(G, e_in) for e_in in G.in_edges(v) ])

def calculate_output_potential(Ginput, v):
	G = Ginput.copy()
	G.add_node(LARGE_INT)

	for n in G.nodes():
		if n >= DEST_INT:
			G.add_edge(n, LARGE_INT, capacity=BIG_CAP, weight=1)

	flowValue, _ = nx.maximum_flow(G, v, LARGE_INT)
	return flowValue

def estimate_output_potential(G, v):
	return np.sum([ cap(G, e_out) for e_out in G.out_edges(v)])


FAST_ESTIMATORS = (estimate_input_potential, estimate_output_potential)
SLOW_ESTIMATORS = (calculate_input_potential, calculate_output_potential)

def calculate_bandwidth(Ginput):
	G = convert_to_di(Ginput.copy())
	G.add_node(-LARGE_INT)
	G.add_node(LARGE_INT)

	for n in G.nodes():
		if n < 0:
			G.add_edge(-LARGE_INT, n, capacity=BIG_CAP, weight=1)
		if n >= DEST_INT:
			G.add_edge(n,LARGE_INT, capacity=BIG_CAP, weight=1)

	flowValue, _ = nx.maximum_flow(G, -LARGE_INT, LARGE_INT)
	return flowValue



def calculate_all_potentials(G, estimators):
	inp = dict([])
	outp = dict([])
	for n in G.nodes():
		if n >= 0 and n < DEST_INT:
			inp[n] = estimators[0](G, n)
			outp[n] = estimators[1](G, n)

	return inp, outp


def WPP(Gfull):
	do_wpp = True
	num_wpp_applied = 0
	G = Gfull.copy()
	while do_wpp:
		do_wpp = False
		for u,v in G.edges_iter():
			if u >= 0 and v < DEST_INT:
				c = cap(G, (u,v))
				cnew = min(estimate_input_potential(G,u), estimate_output_potential(G,v))
				if c > cnew:
					G[u][v]['capacity'] = cnew
					do_wpp = True
					num_wpp_applied += 1
					break

	return G

def DAGOPT(Gfull):
	G = Gfull.copy()
	inp, outp = calculate_all_potentials(G, SLOW_ESTIMATORS)
	for u,v in G.edges_iter():
		if u >= 0 and v < DEST_INT:
			G[u][v]['capacity'] = min([inp[u], outp[v], cap(G, (u,v))])

	return G

			


# routing equivalent


def can_topological(G, u, v):
	total_testl = len(G.in_edges(v,keys=True,data=True))
	total_testr = len(G.out_edges(u,keys=True,data=True))
	return (total_testl <= 1 or total_testr <= 1)



def recover_original_graph_routing(graphs, info, estimators):
	for x in range(len(info)-1, -1, -1):
		mapE = info[x][3]
		uid, vid, kid = (info[x][0], info[x][1], info[x][2])
		for u, v, k in graphs[x].edges_iter(keys=True):
			if u != uid or v != vid or k != kid:
				uu,vv,kk = mapE[(u,v,k)]
				graphs[x][u][v][k]['capacity'] = max(graphs[x+1][uu][vv][kk]['capacity'], graphs[x][u][v][k]['capacity'])

		Gtest = convert_to_di(graphs[x])
		inn = estimators[0](Gtest, uid)
		outt = estimators[1](Gtest, vid)
		graphs[x][uid][vid][kid]['capacity'] = max(graphs[x][uid][vid][kid]['capacity'],  min(inn, outt))


def routing_equivalent_multi(G_input, estimators, is_tradeoff, max_cap = 0):
	randomizer = random.Random(239)
	G = G_input.copy()
	Gbest = G_input.copy()
	Gorigbest = G_input.copy()
	Gsimple = convert_to_di(G)
	inp, outp = calculate_all_potentials(Gsimple, estimators)
	copies = [G_input.copy()]
	info = []
	answers = [full_cap_multi(G)]
	while True:
		edges_candidates = [(u,v,k,d['capacity'], inp[u], outp[v]) for u,v,k,d in G.edges_iter(keys=True,data=True) if u>=0 and v<DEST_INT and u!=v and can_topological(G,u,v) and min(inp[u], outp[v]) < BIG_CAP]
		randomizer.shuffle(edges_candidates)

		if len(edges_candidates) == 0 :
			break

		cand_c = [min(x[4],x[5]) - x[3] for x in edges_candidates]
		id = np.argmin(cand_c)

		(u,v,k,c,inpp, outpp) = edges_candidates[id]

		if c < min(inpp, outpp) and is_tradeoff == False:
			break

		edge_map = { (u,v,k) :  (u,v,k) for u,v,k in G.edges_iter(keys=True) };
		for uu,vv,kk,dd in G.out_edges(v, keys=True, data=True):
			edge_map[(uu, vv, kk)] = (u,vv,len(G.edge[u].get(vv,{})))
			G.add_edge(u, vv, len(G.edge[u].get(vv,{})), dd)

		for uu,vv,kk,dd in G.in_edges(v, keys=True, data=True):
			if uu != u or kk != k:
				edge_map[(uu, vv, kk)] = (uu, u, len(G.edge[uu].get(u,{})))
				G.add_edge(uu, u, len(G.edge[uu].get(u,{})), dd)
		G.remove_node(v)


		if is_tradeoff:
			info.append((u,v,k, edge_map))
			copies.append(G.copy())
			recover_original_graph_routing(copies, info, estimators)
			if full_cap_multi(copies[0]) <= max_cap:
				Gbest = G.copy()
				Gorigbest = copies[0].copy()
			answers.append(full_cap_multi(copies[0]))


		Gsimple = convert_to_di(G)


		if (c < inp[u]):
			to_update = nx.descendants(Gsimple, u).union([u])
			for node in to_update:
				if node < DEST_INT:
					inp[node] = estimators[0](Gsimple, node)

		if (c < outp[v]):
			to_update = nx.ancestors(Gsimple, u).union([u])
			for node in to_update:
				if node >= 0:
					outp[node] = estimators[1](Gsimple, node)


	if not is_tradeoff:
		return G

	recover_original_graph_routing(copies, info, estimators)
	return Gbest, Gorigbest, answers

# bandwith equivalent


def can_bandwith_topological(G, u, v):
	total_testl = len(G.in_edges(v,keys=True,data=True))
	total_testr = len(G.out_edges(u,keys=True,data=True))
	return (total_testl <= 1 or total_testr <= 1)


def recover_original_graph_bandwidth(graphs, info, estimators):
	#G = graphs[len(info)].copy()
	for x in range(len(info)-1, -1, -1):
		mapE = info[x][2]
		costE = info[x][3]
		uid, vid  = (info[x][0], info[x][1])

		for u, v, k in graphs[x].edges_iter(keys=True):
			if u != uid or v != vid:
				uu,vv = mapE[(u,v)]
				cc = costE[(u,v)]
				if cc >= 0:
					graphs[x][u][v][k]['capacity'] = max(graphs[x+1][uu][vv][0]['capacity'] - cc, graphs[x][u][v][k]['capacity'])

		Gtest = convert_to_di(graphs[x])
		inn = estimators[0](Gtest, uid)
		outt = estimators[1](Gtest, vid)
		graphs[x][uid][vid][0]['capacity'] = max(graphs[x][uid][vid][0]['capacity'],  min(inn, outt))


def routing_nonequivalent_multi(G_input, estimators, is_tradeoff, max_cap = 0):
	randomizer = random.Random(239)
	G = G_input.copy()
	Gsimple = convert_to_di(G)
	Gbest = G_input.copy()
	Gorigbest = G_input.copy()
	inp, outp = calculate_all_potentials(Gsimple, estimators)
	copies = [G_input.copy()]
	info = []
	answers = [full_cap_multi(G_input)]
	while True:
		edges_candidates = [(u,v,d['capacity'], inp[u], outp[v]) for u,v,_,d in G.edges_iter(keys=True,data=True) if u>=0 and v<DEST_INT and u!=v and can_bandwith_topological(G,u,v) and  min(inp[u], outp[v]) < BIG_CAP]
		randomizer.shuffle(edges_candidates)
		if len(edges_candidates) == 0 :
			break
		cand_c = [min(x[3],x[4]) - x[2] for x in edges_candidates]
		id = np.argmin(cand_c)

		(u,v,c,inpp, outpp) = edges_candidates[id]
		if c < min(inpp, outpp) and is_tradeoff == False:
			break

		edge_map = { (u,v) :  (u,v) for u,v,k in G.edges_iter(keys=True) };
		cost_map = {}

		Gold = G.copy()
		for uu,vv,kk,dd in G.out_edges(v, keys=True, data=True):
			edge_map[(uu, vv)] = (u,vv)
			G.add_edge(u, vv, len(G.edge[u].get(vv,{})), dd)

		for uu,vv,kk,dd in G.in_edges(v, keys=True, data=True):
			if uu != u:
				edge_map[(uu, vv)] = (uu, u)
				G.add_edge(uu, u, len(G.edge[uu].get(u,{})), dd)

		G.remove_node(v)

		if is_tradeoff:
			for old_u, old_v in Gold.edges_iter():
				new_u,new_v = edge_map[(old_u, old_v)]

				if new_v == new_u or (old_u == u and old_v == v):
					cost_map[(old_u, old_v)] = -1
					continue

				ln = len(G[new_u][new_v])
				assert ln == 2 or ln == 1
				if ln == 1:
					cost_map[old_u, old_v] = 0
				if ln == 2:
					assert new_v == u or new_u == u
					if new_v == u:
						if old_v == v:
							cost_map[(old_u, old_v)] = Gold[old_u][u][0]['capacity']
						else:
							cost_map[(old_u, old_v)] = -1

					if new_u == u:
						if old_u == u:
							cost_map[(old_u, old_v)] = Gold[v][old_v][0]['capacity']
						else:
							cost_map[(old_u, old_v)] = -1


		Gsimple = convert_to_di(G)
		G = convert_to_multi(Gsimple)

		if is_tradeoff:
			info.append((u, v, edge_map, cost_map))
			copies.append(G.copy())
			recover_original_graph_bandwidth(copies, info, estimators)
			if full_cap_multi(copies[0]) <= max_cap:
				Gbest = G.copy()
				Gorigbest = copies[0].copy()
			answers.append(full_cap_multi(copies[0]))


		if c < inp[u]:
			to_update = nx.descendants(Gsimple, u).union([u])
			for node in to_update:
				if node < DEST_INT:
					inp[node] = estimators[0](Gsimple, node)


		if c < outp[v]:
			to_update = nx.ancestors(Gsimple, u).union([u])
			for node in to_update:
				if node >= 0:
					outp[node] = estimators[1](Gsimple, node)

	if not is_tradeoff:
		return G

	for x in range(len(info)-1, -1, -1):
		mapE = info[x][2]
		costE = info[x][3]
		uid, vid  = (info[x][0], info[x][1])
		for u, v, k in copies[x].edges_iter(keys=True):
			if u != uid or v != vid:
				uu,vv = mapE[(u,v)]
				cc = costE[(u,v)]
				if cc >= 0:
					copies[x][u][v][k]['capacity'] = max(copies[x+1][uu][vv][0]['capacity'] - cc, copies[x][u][v][k]['capacity'])

		Gtest = convert_to_di(copies[x])
		inn = estimators[0](Gtest, uid)
		outt = estimators[1](Gtest, vid)
		copies[x][uid][vid][0]['capacity'] = max(copies[x][uid][vid][0]['capacity'],  min(inn, outt))
		


	recover_original_graph_bandwidth(copies, info, estimators)
	return Gbest, Gorigbest, answers

