import os
import argparse
import random
import jsonlines
import re
import ast
import numpy as np
from sklearn.metrics import classification_report
from sklearn.metrics import precision_score, recall_score, f1_score
random.seed(42)
import argparse
import os
import sys
import pytrec_eval


def eval_ranking_pred(label_file, pred_file):
    #
    # load directory structure
    #

    labels = []

    with jsonlines.open(label_file, mode='r') as reader:
        for file in reader:
            labels.append(file)


    label_dict = {}
    for label in labels:
        label_dict.update({label.get('guid'): label.get('label')})

    print(len(labels))
    print(len(label_dict))

    with open(pred_file, 'r') as reader:
        content = reader.read().splitlines()
        predictions = [ast.literal_eval(file) for file in content]

    print(len(predictions))

    pred_dict = {}
    pos = []
    for pred in predictions:
        pred_dict.update({pred.get('guid'): max(pred.get('res'))+ 100 * np.argmax(pred.get('res')) + 100})  # für binary ist hier 1 anstatt 0 (für mseloss output)
        pos.append(min(pred.get('res')))  # für binary ist hier 1 anstatt 0 (für mseloss)

    print(min(pos))
    assert abs(min(pos)) < 100


    files = list(label_dict.keys())
    files.sort()

    qrels = {}
    for file in files:
        qrels.update({file.split('_')[0]: {}})
    for file in files:
        # print(file.split('_')[0])
        qrels.get(file.split('_')[0]).update({file.split('_')[1]: label_dict.get(file)})
        # qrels.update({file.split('_')[0]: {file.split('_')[1]: label_dict.get(file)}})
        # label_dict.get(file)

    # print(qrels.get('001'))

    run = {}
    for file in files:
        run.update({file.split('_')[0]: {}})
    for file in files:
        # print(file.split('_')[0])
        if pred_dict.get(file):
            run.get(file.split('_')[0]).update({file.split('_')[1]: pred_dict.get(file)})
        else:
            run.get(file.split('_')[0]).update({file.split('_')[1]: 0})

    # trec eval

    evaluator = pytrec_eval.RelevanceEvaluator(
        qrels, {'map', 'P_1', 'recall_1', 'P_2', 'recall_2'})

    results = evaluator.evaluate(run)

    def print_line(measure, scope, value):
        print('{:25s}{:8s}{:.4f}'.format(measure, scope, value))

    def write_line(measure, scope, value):
        return '{:25s}{:8s}{:.4f}'.format(measure, scope, value)

    for query_id, query_measures in sorted(results.items()):
        for measure, value in sorted(query_measures.items()):
            print_line(measure, query_id, value)

    # Scope hack: use query_measures of last item in previous loop to
    # figure out all unique measure names.
    #
    # TODO(cvangysel): add member to RelevanceEvaluator
    #                  with a list of measure names.
    for measure in sorted(query_measures.keys()):
        print_line(
            measure,
            'all',
            pytrec_eval.compute_aggregated_measure(
                measure,
                [query_measures[measure]
                 for query_measures in results.values()]))

    with open(pred_file.split('.txt')[0] + '_eval_200_3.txt', 'w') as output:
        for measure in sorted(query_measures.keys()):
            output.write(write_line(
                measure,
                'all',
                pytrec_eval.compute_aggregated_measure(
                    measure,
                    [query_measures[measure]
                     for query_measures in results.values()])) + '\n')


def eval_ranking_bm25(label_file, bm25_folder):
    labels = []

    with jsonlines.open(label_file, mode='r') as reader:
        for file in reader:
            labels.append(file)

    label_dict = {}
    for label in labels:
        label_dict.update({label.get('guid'): label.get('label')})

    files = list(label_dict.keys())
    files.sort()

    qrels = {}
    for file in files:
        qrels.update({file.split('_')[0]: {}})
    for file in files:
        print(file.split('_')[0])
        qrels.get(file.split('_')[0]).update({file.split('_')[1]: label_dict.get(file)})
        # qrels.update({file.split('_')[0]: {file.split('_')[1]: label_dict.get(file)}})
        # label_dict.get(file)

    run = {}
    for file in files:
        run.update({file.split('_')[0]: {}})
    for key in list(run.keys()):
        with open(os.path.join(bm25_folder, 'bm25_top50_{}.txt'.format(key)), #.xml für clef-ip corpus
                  'r') as out:  # (.xml) for clef-ip top 50, different splitting also!
            #text = [text.split('-')[0] + '-' + text.split('-')[1] for text in
            #        [text.split('\n')[0].strip() for text in out.readlines()]]
            text = [text.split('_')[1] for text in
                    [text.split('\n')[0].strip() for text in out.readlines()]]
            for file in files:
                if file.split('_')[1] in text:
                    run.get(key).update(
                        {text[text.index(file.split('_')[1])]: len(text) - text.index(file.split('_')[1])})
                else:
                    run.get(key).update({file.split('_')[1]: 0})

    # trec eval
    evaluator = pytrec_eval.RelevanceEvaluator(
        qrels, {'map', 'P_1', 'recall_1', 'P_2', 'recall_2'})#pytrec_eval.supported_measures

    results = evaluator.evaluate(run)

    def print_line(measure, scope, value):
        print('{:25s}{:8s}{:.4f}'.format(measure, scope, value))

    def write_line(measure, scope, value):
        return '{:25s}{:8s}{:.4f}'.format(measure, scope, value)

    for query_id, query_measures in sorted(results.items()):
        for measure, value in sorted(query_measures.items()):
            print_line(measure, query_id, value)

    # Scope hack: use query_measures of last item in previous loop to
    # figure out all unique measure names.
    #
    # TODO(cvangysel): add member to RelevanceEvaluator
    #                  with a list of measure names.
    for measure in sorted(query_measures.keys()):
        print_line(
            measure,
            'all',
            pytrec_eval.compute_aggregated_measure(
                measure,
                [query_measures[measure]
                 for query_measures in results.values()]))

    with open(os.path.join(bm25_folder, 'eval_bm25_200_3.txt'), 'w') as output:
        for measure in sorted(query_measures.keys()):
            output.write(write_line(
                measure,
                'all',
                pytrec_eval.compute_aggregated_measure(
                    measure,
                    [query_measures[measure]
                     for query_measures in results.values()])) + '\n')


if __name__ == "__main__":
    #
    # config
    #
    parser = argparse.ArgumentParser()

    parser.add_argument('--label-file', action='store', dest='label_file',
                        help='org file with the guid and the labels', required=True)
    parser.add_argument('--pred-file', action='store', dest='pred_file',
                        help='file with the binary prediction per guid', required=False)
    parser.add_argument('--bm25-folder', action='store', dest='bm25_folder',
                        help='folder with the BM25 retrieval per guid which the result is compared to', required=False)
    args = parser.parse_args()

    #label_file = '/mnt/c/Users/sophi/Documents/phd/data/clef-ip/2011_prior_candidate_search/clef-ip-2011_PACTest/test_org_top50_wogold.json'
    #pred_file = '/mnt/c/Users/sophi/Documents/phd/data/clef-ip/2011_prior_candidate_search/clef-ip-2011_PACTest/output/output_test_top50_wogold_patentbert_patentattengru.txt'

    #label_file = '/mnt/c/Users/sophi/Documents/phd/data/coliee2019/task1/task1_test/test_org_200.json'
    #pred_file = '/mnt/c/Users/sophi/Documents/phd/data/coliee2019/task1/task1_test/output/output_colieedata_test_top50_wogold_bertorg_lawattenlstm.txt'

    # bm25 labels: from bm25_folder
    #bm25_folder = '/mnt/c/Users/sophi/Documents/phd/data/clef-ip/2011_prior_candidate_search/clef-ip-2011_PACTest/bm25_top50'
    #bm25_folder = '/mnt/c/Users/sophi/Documents/phd/data/coliee2019/task1/task1_test/task1_test_bm25_top50'

    if args.pred_file:
        eval_ranking_pred(args.label_file, args.pred_file)
    if args.bm25_folder:
        eval_ranking_bm25(args.label_file, args.bm25_folder)




