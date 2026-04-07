from typing import Optional

import torch
import pytorch_lightning as pl
from yacs.config import CfgNode
from .dataset_keypoints import DatasetKeypoints

class DataModule(pl.LightningDataModule):

    def __init__(self, cfg: CfgNode, dataset_cfg: CfgNode) -> None:

        super().__init__()
        self.cfg = cfg
        self.dataset_cfg = dataset_cfg
        self.train_dataset = None
        self.val_dataset = None
        self.test_dataset = None
        self.mocap_dataset = None

    def setup(self, stage: Optional[str] = None):
        self.train_dataset = self.train_dataset_prepare()
        self.val_dataset = self.val_dataset_prepare()

    def train_dataset_prepare(self):
        if self.cfg.DATASETS.DATASETS_AND_RATIOS:
            dataset_names = self.cfg.DATASETS.DATASETS_AND_RATIOS.split('_')
            dataset_list = [DatasetKeypoints(self.cfg, ds) for ds in dataset_names]
            train_ds = torch.utils.data.ConcatDataset(dataset_list)
            return train_ds
        else:
            return None

    def val_dataset_prepare(self):
        dataset_names = self.cfg.DATASETS.VAL_DATASETS.split('_')
        dataset_list = [DatasetKeypoints(self.cfg, ds, is_train=False) for ds in dataset_names]
        return dataset_list

    def train_dataloader(self):
        train_dataloader = torch.utils.data.DataLoader(self.train_dataset, self.cfg.TRAIN.BATCH_SIZE, drop_last=True, shuffle=True, num_workers=self.cfg.GENERAL.NUM_WORKERS, prefetch_factor=self.cfg.GENERAL.PREFETCH_FACTOR)
        return {'img': train_dataloader}

    def val_dataloader(self):
        val_dataloaders = []
        for val_ds in self.val_dataset:
            val_dataloaders.append(torch.utils.data.DataLoader(val_ds, self.cfg.TRAIN.BATCH_SIZE, drop_last=True, num_workers=self.cfg.GENERAL.NUM_WORKERS))
        return val_dataloaders

    def test_dataloader(self):
        val_dataloaders = []
        for val_ds in self.val_dataset:
            val_dataloaders.append(torch.utils.data.DataLoader(val_ds, self.cfg.TRAIN.BATCH_SIZE, drop_last=True, num_workers=self.cfg.GENERAL.NUM_WORKERS))
        return val_dataloaders
