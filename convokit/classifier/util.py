from convokit.model import Corpus, Conversation, Utterance, User, CorpusObject
from typing import List, Union, Callable
import pandas as pd
from scipy.sparse import csr_matrix
import numpy as np


def extract_feats_from_obj(obj: CorpusObject, pred_feats: List[str]):
    """
    Assuming feature data has at most one level of nesting, i.e. meta['height'] = 1, and meta['grades'] = {'prelim1': 99,
    'prelim2': 75, 'final': 100}
    Extract the features values from a Corpus object
    :param obj: Corpus object
    :param pred_feats: list of features to extract metadata for
    :return: dictionary of predictive feature names to values
    """
    retval = dict()
    for feat_name in pred_feats:
        feat_val = obj.meta[feat_name]
        if type(feat_val) == dict:
            retval.update(feat_val)
        else:
            retval[feat_name] = feat_val
    return retval


def extract_feats_dict(corpus: Corpus, obj_type: str, pred_feats: List[str],
                       selector: Callable[[CorpusObject], bool] = lambda x: True):
    """
    Extract features dictionary from a corpus
    :param corpus: target corpus
    :param obj_type: Corpus object type
    :param pred_feats: list of features to extract metadata for
    :param selector: function to select for Corpus objects to extract features from
    :return: dictionary mapping object id to a dictionary of predictive features
    """
    obj_id_to_feats = {obj.id: extract_feats_from_obj(obj, pred_feats) for obj in corpus.iter_objs(obj_type, selector)}

    return obj_id_to_feats


def extract_feats(corpus: Corpus, obj_type: str, pred_feats: List[str],
                  selector: Callable[[CorpusObject], bool] = lambda x: True):
    """
    Extract a matrix representation of Corpus objects' features from corpus
    :param corpus: target corpus
    :param obj_type: Corpus object type
    :param pred_feats: list of features to extract metadata for
    :param selector: function to select for Corpus objects to extract features from
    :return: matrix of Corpus objects' features
    """
    obj_id_to_feats = extract_feats_dict(corpus, obj_type, pred_feats, selector)
    feats_df = pd.DataFrame.from_dict(obj_id_to_feats, orient='index')
    return csr_matrix(feats_df.values)


def extract_label_dict(corpus: Corpus, obj_type: str, labeller: Callable[[CorpusObject], bool],
                       selector: Callable[[CorpusObject], bool] = lambda x: True):
    """
    Generate dictionary mapping Corpus object id to label from corpus
    :param corpus: target corpus
    :param obj_type: Corpus object type
    :param labeller: function that takes a Corpus object as input and outputs its label
    :param selector: function to select for Corpus objects to extract features from
    :return: dictionary mapping Corpus object id to label
    """
    obj_id_to_label = dict()
    for obj in corpus.iter_objs(obj_type, selector):
        obj_id_to_label[obj.id] = {'y': 1} if labeller(obj) else {'y': 0}

    return obj_id_to_label


def extract_feats_and_label(corpus: Corpus, obj_type: str, pred_feats: List[str],
                            labeller: Callable[[CorpusObject], bool],
                            selector: Callable[[CorpusObject], bool] = None):
    """
    Extract matrix of predictive features and numpy array of labels from corpus
    :param corpus: target Corpus
    :param obj_type: Corpus object type
    :param pred_feats: list of features to extract metadata for
    :param labeller: function that takes a Corpus object as input and outputs its label
    :param selector: function to select for Corpus objects to extract features from
    :return: matrix of predictive features and numpy array of labels
    """
    obj_id_to_feats = extract_feats_dict(corpus, obj_type, pred_feats, selector)
    obj_id_to_label = extract_label_dict(corpus, obj_type, labeller, selector)

    X_df = pd.DataFrame.from_dict(obj_id_to_feats, orient='index')
    y_df = pd.DataFrame.from_dict(obj_id_to_label, orient='index')

    X_y_df = pd.concat([X_df, y_df], axis=1, sort=False)

    y = X_y_df['y']
    X = X_y_df.drop(columns='y')

    return csr_matrix(X.values), np.array(y)


def get_coefs_helper(clf, feature_names: List[str] = None, coef_func=None):
    """
    Get dataframe of classifier coefficients. By default, assumes it is a pipeline with a logistic regression component
    :param clf: classifier model
    :param feature_names: list of feature names to get coefficients for
    :param coef_func: function for accessing the list of coefficients from the classifier model
    :return: DataFrame of features and coefficients, indexed by feature names
    """
    if coef_func is None:
        coefs = clf.named_steps['logreg'].coef_[0].tolist()
    else:
        coefs = coef_func(clf)

    assert len(feature_names) == len(coefs)
    feats_coefs = sorted(list(zip(feature_names, coefs)), key=lambda x: x[1], reverse=True)
    return pd.DataFrame(feats_coefs, columns=['feat_name', 'coef'])\
                        .set_index('feat_name').sort_values('coef', ascending=False)





