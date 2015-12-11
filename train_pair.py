from disambiguation import find_unique_characters
from evaluation import evaluate_candidates
from labeling import get_sparknote_characters_from_file
from matplotlib import pyplot as plt
from optparse import OptionParser
import numpy as np
import os, random, re
from train_common import *

FEATURES_DIR = 'features'
LABELS_DIR = 'labels'
PAIR_FEATURES_EXTENSION = '_pair_features_readable.txt'
PAIR_LABELS_EXTENSION = '_non_unique_relations.txt'

DEFAULT_FILTER = [
  #'cooc.*'
  #'cooc.*', 'book.*', 'count.*', '.*cap'
  #'coref_shorter_count_norm_char'
]

def evaluate_pair(clf, book, scaler = None):
    print book
    X, y, cands = get_pair_data([book])
    if scaler != None:
        X = scaler.transform(X)

    y_pred = clf.predict(X)
    print 'Non unqiue Precision:', precision(y_pred, y), 'Non unique Recall:', recall(y_pred, y)
    return 0

def get_pair_data(books, print_features=False):
    return get_data(books, FEATURES_DIR, PAIR_FEATURES_EXTENSION, LABELS_DIR, PAIR_LABELS_EXTENSION, PAIR_FEATURE_FILTER, print_features)

def train_and_test(train_books, test_books, train, scale=True):
    X_train, y_train, cands_train = get_pair_data(train_books, True)
    X_test, y_test, cands_test = get_pair_data(test_books) 
    
    scaler = None
    if scale:
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
    
    print sum(y_train)*0.1/len(y_train)
    print 'Start training'
    print X_train.shape
    clf = train(X_train, y_train)
    print 'Done training'
    y_train_pred = clf.predict(X_train)
    y_test_pred = clf.predict(X_test)
   
    '''
    # print performance for training books
    print "--------------Traning data-------------"
    train_perf = evaluate_books(clf, train_books, scaler, evaluate_pair)
   
   # print performance for testing books 
    print "\n"
    print "--------------Testing data-------------"
    test_perf = evaluate_books(clf, test_books, scaler, evaluate_pair)
    ''' 
    print 'Train Non-unique Precision:', precision(y_train_pred, y_train), 'Non-unique Recall:', recall(y_train_pred, y_train)
    print 'Test Non-unique Precision:', precision(y_test_pred, y_test), 'Recall:', recall(y_test_pred, y_test)
    return clf, scaler, X_train, y_train, X_test, y_test

# traning methods for different training models
def train_svm(X, y):
    clf = svm.SVC(kernel=kernel, degree=degree, class_weight=class_weight)
    clf.fit(X, y)
    return clf

# random forest
def train_rf(X, y):
    clf = RandomForestClassifier(n_estimators=n_estimators, max_depth = max_depth, class_weight=class_weight)
    clf.fit(X,y)
    return clf

# extra random forest
def train_erf(X, y):
    clf = ExtraTreesClassifier(n_estimators=n_estimators, max_depth = max_depth, class_weight=class_weight)
    clf.fit(X,y)
    return clf

# ada_boost
def train_ada_boost(X, y):
    clf = AdaBoostClassifier(n_estimators=n_estimators)
    clf.fit(X,y)
    return clf

# ada_boost
def train_grad_boost(X, y):
    clf = GradientBoostingClassifier(n_estimators=n_estimators)
    clf.fit(X,y)
    return clf

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-d', '--feature_dir', help="feature directory", dest="feature_directory", default=FEATURES_DIR)
    parser.add_option('-e', '--feature_extension', help="feature extension", dest="feature_extension", default=PAIR_FEATURES_EXTENSION)
    parser.add_option('-l', '--label_dir', help='label directory', dest='label_directory', default=LABELS_DIR)
    parser.add_option('-f', '--feature_filter', help='feature filter', dest='feature_filter', default=str(DEFAULT_FILTER))
    parser.add_option('-s', '--train_test_split', help='Ratio of training books', dest='train_ratio', default='0.7')
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False)
    parser.add_option("-m", "--model", dest="model")
    parser.add_option("-k", "--kernel", dest="kernel", default='rbf')
    parser.add_option("--seed", dest="seed", default='None')

    ################## hyper-parameters for models #################
    # degree for polynomial kernel for svm
    parser.add_option("--degree", dest="degree", default=2)
    # a bias term to adjust tradeoff between precision and recall,
    # the higher bias, the higher recall and lower precision
    parser.add_option("-b", "--bias", dest="bias", default=1)
    # for random forest, adaboost, and gradboost
    # suggest 10 for random forest, 100 for adaboost and gradboost
    parser.add_option("-n", "--n_estimators", dest="n_estimators", default=10)
    # for random forest
    parser.add_option("--max_depth", dest="max_depth", default='None')
    
    # parse options
    (options, args) = parser.parse_args()
    FEATURES_DIR=options.feature_directory
    FEATURES_EXTENSION=options.feature_extension
    LABELS_DIR=options.label_directory
    filters = eval(options.feature_filter)
    verbose = options.verbose

    PAIR_FEATURE_FILTER = '|'.join('^%s$' % f for f in filters)
    
    # set traning options
    kernel = options.kernel
    degree = int(options.degree)
    train_books, test_books = generate_train_test(float(options.train_ratio), options.seed, FEATURES_DIR)
    #train_books = list(train_books)[:20]
    #test_books = list(test_books)[:20]
    train_method = locals()['train_%s' % options.model]
    class_weight = {1:float(options.bias), 0:1}
    n_estimators = int(options.n_estimators)
    max_depth = eval(options.max_depth)

    (clf, scaler, X_train, y_train, X_test, y_test) = train_and_test(train_books, test_books, train_method)