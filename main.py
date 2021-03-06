import networkx as nx
import random
import glob
import sys
import numpy as np
from datetime import datetime,time,date,timedelta


from graph_heuristics import *

in_dir = sys.argv[1]

num_sources = 5
num_destinations = 5
if len(sys.argv) > 3:
	num_sources = int(sys.argv[2])
	num_destinations = int(sys.argv[3])


out_f1 = open(in_dir+".results", "w+")



def print_statistics(lists, file, norm):
	n = max(len(lists[0]),len(lists[1]),len(lists[2]),len(lists[3]))
	for i in range(0,n):
		print >> file, "%d" % i,
		for j in range(0,4):
			if (j < 3) :
				print>> file, ("%.3f" % (1.0*lists[j][i]/norm) if i < len(lists[j]) else "nan"),
			else:
				print >> file, ("%.3f" % (1.0 * lists[j][i] / norm) if i < len(lists[j]) else "nan")



for in_fname in glob.glob(in_dir + '/graph*.txt'):
	print(in_fname)
	Gfull = read_graph(in_fname)
	Gfull = simplify(Gfull)
	if not validate_topology(Gfull):
		continue

	Gfull_m = convert_to_multi(Gfull)
	Gdagopt = DAGOPT(Gfull)
	Gwpp = WPP(Gfull)

	Gdagopt_m = convert_to_multi(Gdagopt)
	Gwpp_m = convert_to_multi(Gwpp)

	G_req_fast = routing_equivalent_multi(Gwpp_m, FAST_ESTIMATORS, False)
	G_req_slow = routing_equivalent_multi(Gdagopt_m, SLOW_ESTIMATORS, False)

	Greq_best_fast, Greq_best_fast_orig, answers_req_fast = routing_equivalent_multi(Gwpp_m, FAST_ESTIMATORS, True, max_cap=full_cap(Gfull))
	Greq_best_slow, Greq_best_slow_orig, answers_req_slow = routing_equivalent_multi(Gdagopt_m, SLOW_ESTIMATORS, True, max_cap=full_cap(Gfull))

	req_coef_fast = 1.0*calculate_bandwidth(Greq_best_fast_orig) / calculate_bandwidth(Gfull_m)
	req_coef_slow = 1.0*calculate_bandwidth(Greq_best_slow_orig) / calculate_bandwidth(Gfull_m)

	G_band_fast = routing_nonequivalent_multi(Gwpp_m, FAST_ESTIMATORS, False)
	G_band_slow = routing_nonequivalent_multi(Gdagopt_m, SLOW_ESTIMATORS, False)

	Gband_best_fast, Gband_best_fast_orig, answers_band_fast = routing_nonequivalent_multi(Gwpp_m, FAST_ESTIMATORS, True, max_cap=full_cap(Gfull))
	Gband_best_slow, Gband_best_slow_orig, answers_band_slow = routing_nonequivalent_multi(Gdagopt_m, SLOW_ESTIMATORS, True, max_cap=full_cap(Gfull))

	band_coef_fast = 1.0*calculate_bandwidth(Gband_best_fast_orig) / calculate_bandwidth(Gfull_m)
	band_coef_slow = 1.0*calculate_bandwidth(Gband_best_slow_orig) / calculate_bandwidth(Gfull_m)


	print >> out_f1, '_'.join(in_fname.split('.')[1:-1]).replace('_', '\_')

	print >> out_f1, "% Table 1 values" 
	tuple_toprint = (num_nodes(Gfull), num_edges(Gfull), full_cap(Gfull), full_cap(Gdagopt), full_cap(Gwpp),
                  num_nodes(G_req_slow), num_edges(G_req_slow), 
                  num_nodes(G_req_fast), num_edges(G_req_fast), 
                  num_nodes(G_band_slow), num_edges(G_band_slow),
                  num_nodes(G_band_fast), num_edges(G_band_fast))
	print >> out_f1, ('& %d ' * len(tuple_toprint)+"\\\\") % tuple_toprint

	print >> out_f1, "% Table 2 values" 
	tuple_toprint = (num_nodes(Gfull), num_edges(Gfull), 
                  num_nodes(Greq_best_slow), num_edges(Greq_best_slow), req_coef_slow,
                  num_nodes(Greq_best_fast), num_edges(Greq_best_fast), req_coef_fast,
                  num_nodes(Gband_best_slow), num_edges(Gband_best_slow), band_coef_slow,
                  num_nodes(Gband_best_fast), num_edges(Gband_best_fast), band_coef_fast)
	print >> out_f1, ('& %d & %d '+ '& %d & %d & %.2f '* 4 +"\\\\") % tuple_toprint

	print >> out_f1, "% Figure 3 lines" 
	print_statistics([answers_req_slow, answers_req_fast, answers_band_slow, answers_band_fast], out_f1, full_cap(Gfull)) 
	out_f1.flush()

out_f1.close()

exit(0)

