from determined.experimental import Determined
from PIL import Image
import numpy as np
import torch
import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

from torchvision.transforms import Compose, ToTensor

def get_transform():
    transforms = []
    transforms.append(ToTensor())
    return Compose(transforms)


class PedDetectionModel(object):
    """
    Model template. You can load your model parameters in __init__ from a location accessible at runtime
    """

    def __init__(self, det_master=None, experiment_id=None):
        """
        Add any initialization parameters. These will be passed at runtime from the graph definition parameters defined in your seldondeployment kubernetes resource manifest.
        """
        logging.info(f"Loading checkpoint {experiment_id} from master at {det_master}")
        checkpoint = Determined(master=det_master).get_experiment(experiment_id).top_checkpoint()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = checkpoint.load(map_location=self.device)
        self.model.eval()
        logging.info("Loaded checkpoint")
        self.transform = get_transform()

    def predict(self, X, features_names=None):
        """
        Return a prediction.

        Parameters
        ----------
        X : array-like
        feature_names : array of feature names (optional)
        """
        logging.info("Request Received")
        with torch.no_grad():
            image = self.transform(Image.fromarray(X.astype(np.uint8)))
            preds = self.model(image.unsqueeze(0).to(self.device))[0]
        boxes = preds['boxes'].cpu().numpy().tolist()
        labels = preds['labels'].cpu().numpy().tolist()
        scores = preds['scores'].cpu().numpy().tolist()
        return {"prediction": {"boxes": boxes, "labels": labels, "scores": scores}}
