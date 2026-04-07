import torch.nn as nn
from .backbone.utils import get_backbone_info
from .backbone.hrnet import hrnet_w48

class FLNet(nn.Module):
    def __init__(self):

        super(FLNet, self).__init__()

        self.backbone = hrnet_w48(
            pretrained_ckpt_path='',
            downsample=True,
            use_conv=True,
        ) 

        num_input_features = 720
        self.avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc1 = nn.Linear(num_input_features, 1024)
        self.drop1 = nn.Dropout()
        self.fc2 = nn.Linear(1024, 1024)
        self.drop2 = nn.Dropout()
        self.fc3 = nn.Linear(1024, 2)
        nn.init.xavier_uniform_(self.fc3.weight, gain=0.1)


    def forward(
            self,
            images,
    ):
        features = self.backbone(images)
        xf = self.avgpool(features)
        xf = xf.view(xf.size(0), -1)
        xc = self.fc1(xf)
        xc = self.drop2(xc)
        xc = self.fc3(xc)
        return xc, xf