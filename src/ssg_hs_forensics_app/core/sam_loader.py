from segment_anything import sam_model_registry

def load_sam_model(model_type: str, checkpoint_path: str):
    sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
    sam.eval()
    return sam
