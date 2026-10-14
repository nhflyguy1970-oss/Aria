"""ARIA's ComfyUI nodes, loaded through ``--extra-model-paths-config comfy_nodes/extra_paths.yaml``
(the ComfyUI install itself is not modified).

ARIA runs ComfyUI with ``--lowvram`` (the Phase 8 qualified Flux profile), which also puts
every text encoder on the CPU. For Qwen-Image's 7B Qwen2.5-VL encoder that meant ~58 s of
fp32 CPU encoding per job (2026-10-14). This loader runs one encoder on the RTX for the
encode and offloads it to system RAM afterwards like any model; it is used only by ARIA's
Qwen-Image workflow, inside ARIA's exclusive RTX image slot.
"""
import comfy.model_management as mm
import comfy.sd
import folder_paths
import nodes


class ARIATextEncoderLoaderGPU:
    @classmethod
    def INPUT_TYPES(cls):
        types = nodes.CLIPLoader.INPUT_TYPES()["required"]["type"]
        return {"required": {"clip_name": (folder_paths.get_filename_list("text_encoders"),), "type": types}}

    RETURN_TYPES = ("CLIP",)
    FUNCTION = "load_clip"
    CATEGORY = "advanced/loaders"
    DESCRIPTION = "CLIPLoader that encodes on the GPU even under --lowvram (ARIA Qwen-Image)."

    def load_clip(self, clip_name, type="qwen_image"):
        clip_type = getattr(comfy.sd.CLIPType, type.upper(), comfy.sd.CLIPType.STABLE_DIFFUSION)
        model_options = {"load_device": mm.get_torch_device(), "offload_device": mm.text_encoder_offload_device()}
        clip_path = folder_paths.get_full_path_or_raise("text_encoders", clip_name)
        clip = comfy.sd.load_clip(ckpt_paths=[clip_path], embedding_directory=folder_paths.get_folder_paths("embeddings"),
                                  clip_type=clip_type, model_options=model_options)
        return (clip,)


NODE_CLASS_MAPPINGS = {"ARIATextEncoderLoaderGPU": ARIATextEncoderLoaderGPU}
NODE_DISPLAY_NAME_MAPPINGS = {"ARIATextEncoderLoaderGPU": "Load Text Encoder on GPU (ARIA)"}
