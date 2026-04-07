import pytorch_lightning as pl
from .backbones import create_backbone
from .heads.smpl_head_keypoints import build_keypoints_head

class DenseKP(pl.LightningModule):

    def __init__(self):
        super().__init__()
        self.backbone = create_backbone()
        self.head = build_keypoints_head()

    def forward(self, batch)
        x = batch['img']
        batch_size = x.shape[0]

        conditioning_feats = self.backbone(x[:,:,:,32:-32])
        output = self.head(conditioning_feats)
        return output
   