#!/usr/bin/env python3
# /Users/vanshshah/Desktop/OWLmarketing/video_generation/train_model.py

import os
import glob
import logging
import torch
import torchvision.transforms as T
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from diffusers import StableDiffusionPipeline, DDPMScheduler
from accelerate import Accelerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# Directory containing competitor reels frames
DATA_DIR = "/Users/vanshshah/Desktop/OWLmarketing/video_generation/data"
# Base model to fine-tune (SDXL 1.0)
BASE_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
# Directory where the fine-tuned model will be saved
OUTPUT_DIR = "./trained_model_prod"

class CompetitorDataset(Dataset):
    """
    Dataset for loading training images (frames) extracted from competitor reels.
    Expects images to be in PNG or JPG format.
    """
    def __init__(self, data_dir, transform=None):
        self.data_dir = data_dir
        self.image_files = glob.glob(os.path.join(data_dir, "*.png"))
        self.image_files += glob.glob(os.path.join(data_dir, "*.jpg"))
        self.transform = transform

    def __len__(self):
        return len(self.image_files)
    
    def __getitem__(self, idx):
        img_path = self.image_files[idx]
        image = Image.open(img_path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image

def train_dreambooth(
    data_dir: str,
    base_model: str = BASE_MODEL,
    output_dir: str = OUTPUT_DIR,
    instance_prompt: str = "a photo of a competitor reel showing phone open and app UI, ultra realistic, 8k uhd, highly detailed facial features, professional photography, cinematic lighting",
    learning_rate: float = 1e-6,  # Reduced learning rate for SDXL
    batch_size: int = 1,  # Reduced batch size due to SDXL's larger memory requirements
    num_train_epochs: int = 2  # Reduced epochs as SDXL converges faster
):
    """
    Fine-tune the base Stable Diffusion XL model using competitor reels data.
    This function simulates a DreamBooth-style training loop.
    
    Args:
        data_dir (str): Directory with training images.
        base_model (str): Hugging Face model ID for the base model.
        output_dir (str): Directory to save the fine-tuned model.
        instance_prompt (str): Prompt describing the desired style.
        learning_rate (float): Learning rate for the optimizer.
        batch_size (int): Batch size for training.
        num_train_epochs (int): Number of training epochs.
        
    Returns:
        str: Directory path of the saved fine-tuned model.
    """
    logging.info("Loading training dataset from %s", data_dir)
    transform = T.Compose([
        T.Resize((1024, 1024)),  # SDXL uses 1024x1024 resolution
        T.ToTensor(),
        T.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
    ])
    dataset = CompetitorDataset(data_dir, transform=transform)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    total_steps = len(dataloader) * num_train_epochs
    logging.info("Found %d images, Total training steps: %d", len(dataset), total_steps)

    logging.info("Loading base model: %s", base_model)
    accelerator = Accelerator()
    pipe = StableDiffusionPipeline.from_pretrained(
        base_model,
        torch_dtype=torch.float16,
        use_safetensors=True
    )
    pipe.scheduler = DDPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    device = accelerator.device
    pipe = pipe.to(device)
    pipe.unet.train()

    # Enable memory efficient attention
    if torch.cuda.is_available():
        pipe.enable_xformers_memory_efficient_attention()

    optimizer = torch.optim.AdamW(pipe.unet.parameters(), lr=learning_rate)

    # Training loop with SDXL optimizations
    for epoch in range(num_train_epochs):
        logging.info("Starting epoch %d/%d", epoch+1, num_train_epochs)
        for step, images in enumerate(dataloader):
            with accelerator.accumulate(pipe.unet):
                images = images.to(device)
                # Simulate adding noise and predicting it (replace with actual denoising loss)
                noise = torch.randn_like(images)
                loss = torch.nn.functional.mse_loss(images, noise)
                optimizer.zero_grad()
                accelerator.backward(loss)
                optimizer.step()
                logging.info("Epoch %d, Step %d/%d: Loss = %f", epoch+1, step+1, len(dataloader), loss.item())
        logging.info("Epoch %d complete.", epoch+1)

    accelerator.wait_for_everyone()
    if accelerator.is_main_process:
        os.makedirs(output_dir, exist_ok=True)
        pipe.save_pretrained(output_dir)
        logging.info("Fine-tuned model saved to %s", output_dir)
    return output_dir

if __name__ == "__main__":
    if not os.path.exists(DATA_DIR):
        logging.error("Data directory %s does not exist. Please ensure your competitor frames are placed there.", DATA_DIR)
    else:
        train_dreambooth(DATA_DIR)
