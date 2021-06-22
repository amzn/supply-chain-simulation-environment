"""
Utility for loading datasets as Dataframes from their source files.
This also abstracts the fact that they are CSV.
"""
from os.path import dirname, join, isfile
import os
import pandas
import json
import logging
import boto3

logger = logging.getLogger(__name__)

"""
Datasets are simply modeled as files in S3. We do not, currently, treat
datasets as date-based partitions in AWS Glue, which we may be forced to do as
we expand the support for new datasets.
"""

#Note you need to replace these (bucket, folder, filename) for your aws account
_BUCKET_NAME = 'YOUR_BUCKET_NAME_HERE'
_FOLDER_NAME = 'datasets/'
_SHIPCOST_ESTIMATOR = 'SHIPCOST_DATA_EXAMPLE.csv'


def _download_s3_file(filename):
    module_path = dirname(__file__)

    logger.info("Downloading S3 file = {}.".format(filename))

    # Catch two common cases so that we can log better messages, otherwise let the other exceptions
    # flow through.
    try:
        s3 = boto3.client('s3')
        s3.download_file(_BUCKET_NAME, join(_FOLDER_NAME, filename), join(module_path, filename))
    except MemoryError:
        msg = "Out of memory loading dataset {}.".format(name)
        logger.error(msg)
        raise ValueError(msg)
    except FileNotFoundError:
        msg = "Error loading dataset {} from S3. You may not have the right credentials.".format(name)
        logger.error(msg)
        raise ValueError(msg)


def _load_csv(filename, date_columns = None, dtypes = None, low_memory = False, asin_list = []):
    module_path = dirname(__file__)
    fpath = join(module_path, filename)

    if not isfile(fpath):
        # Let's download the file locally, this not only expedites future use, but also allows people to more
        # easily play with the dataset.
        logger.info("Couldn't find local filepath = {}.".format(fpath))
        _download_s3_file(filename)

    if low_memory == True:
        iter_csv = pandas.read_csv(fpath, iterator=True, chunksize=1000)
        df = pandas.concat([chunk[chunk['asin'].isin(asin_list)] for chunk in iter_csv])
    else:
        df = pandas.read_csv(fpath, parse_dates = date_columns, dtype = dtypes)

    return df

def _load_json(filename):
    module_path = dirname(__file__)
    fpath = join(module_path, filename)

    if not isfile(fpath):
        # Let's download the file locally, this not only expedites future use, but also allows people to more
        # easily play with the dataset.
        _download_s3_file(filename)

    with open(fpath) as f:
        data = json.load(f)

    return data

def load_shipcost_estimator(asin_list):
    return _load_csv(_SHIPCOST_ESTIMATOR)

