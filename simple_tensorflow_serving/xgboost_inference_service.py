from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import time
import numpy as np
import pickle

from .abstract_inference_service import AbstractInferenceService

logger = logging.getLogger("simple_tensorflow_serving")


class XgboostInferenceService(AbstractInferenceService):
  """
  The service to load XGBoost model and make inference.
  """

  def __init__(self, model_name, model_base_path):
    """
    Initialize the service.
        
    Args:
      model_name: The name of the model.
      model_base_path: The file path of the model.
    Return:
      None
    """

    super(XgboostInferenceService, self).__init__()

    self.model_name = model_name
    self.model_base_path = model_base_path
    self.model_version_list = [1]
    self.model_graph_signature = ""
    self.platform = "XGBoost"

    # TODO: Import as needed and only once
    import xgboost as xgb
    from sklearn.externals import joblib

    self.bst = xgb.Booster()

    # Load model
    if self.model_base_path.endswith(".joblib"):
      self.bst = joblib.load(self.model_base_path)
    elif self.model_base_path.endswith(
        ".pkl") or self.model_base_path.endswith(".pickle"):
      with open(self.model_base_path, 'r') as f:
        self.bst = pickle.load(f)
    elif self.model_base_path.endswith(
        ".bst") or self.model_base_path.endswith(".bin"):
      self.bst.load_model(self.model_base_path)
    else:
      logger.error(
          "Unsupported model file format: {}".format(self.model_base_path))

    self.model_graph_signature = "score: {}\nfscore: {}".format(
        self.bst.get_score(), self.bst.get_fscore())


  def inference(self, json_data):
    """
    Make inference with the current Session object and JSON request data.
        
    Args:
      json_data: The JSON serialized object with key and array data.
                 Example is {"model_version": 1, "data": {"keys": [[1.0], [2.0]], "features": [[10, 10, 10, 8, 6, 1, 8, 9, 1], [6, 2, 1, 1, 1, 1, 7, 1, 1]]}}.
    Return:
      The dictionary with key and array data.
      Example is {"keys": [[11], [2]], "softmax": [[0.61554497, 0.38445505], [0.61554497, 0.38445505]], "prediction": [0, 0]}.
    """

    # 1. Build inference data
    import xgboost as xgb
    request_ndarray_data = xgb.DMatrix(np.array(json_data["data"]))

    # 2. Do inference
    start_time = time.time()
    predict_result = self.bst.predict(request_ndarray_data)
    logger.debug("Inference time: {} s".format(time.time() - start_time))

    # 3. Build return data
    result = {
        "result": predict_result,
    }
    logger.debug("Inference result: {}".format(result))

    return result
