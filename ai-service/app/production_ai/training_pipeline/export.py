"""
PyTorch to ONNX and TensorFlow Lite (TFLite) Quantization Pipeline
"""

import os
import logging
import torch
import numpy as np

logger = logging.getLogger(__name__)

def export_to_onnx(pytorch_model: torch.nn.Module, dummy_input: torch.Tensor, output_path: str):
    """Exports PyTorch model weights to ONNX standard format."""
    try:
        torch.onnx.export(
            pytorch_model, 
            dummy_input, 
            output_path, 
            opset_version=12, 
            input_names=["input"], 
            output_names=["output"],
            dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}}
        )
        logger.info(f"[Export] Successfully compiled ONNX graph at {output_path}")
    except Exception as e:
        logger.warning(f"[Export] ONNX export failed: {e}")

def convert_onnx_to_tflite_quantized(onnx_path: str, tflite_path: str):
    """Compiles ONNX to TFLite with Full INT8 Quantization."""
    try:
        import onnx
        from onnx_tf.backend import prepare
        import tensorflow as tf
        
        # Load ONNX graph and convert to TF Graph representation
        onnx_model = onnx.load(onnx_path)
        tf_rep = prepare(onnx_model)
        tf_model_path = tflite_path.replace(".tflite", "_tf")
        tf_rep.export_graph(tf_model_path)
        
        # Quantize TensorFlow Graph to INT8 TFLite representation
        converter = tf.lite.TFLiteConverter.from_saved_model(tf_model_path)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        def representative_dataset():
            for _ in range(50):
                # Calibration dataset
                data = np.random.rand(1, 3, 224, 224).astype(np.float32)
                yield [data]
                
        converter.representative_dataset = representative_dataset
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
        
        tflite_quant_model = converter.convert()
        
        with open(tflite_path, "wb") as f:
            f.write(tflite_quant_model)
        logger.info(f"[Export] Saved Full INT8 Quantized TFLite model at {tflite_path}")
    except Exception as e:
        logger.warning(f"[Export] TFLite Quantization failed: {e}. PyTorch model can still run natively on CPUs/GPUs.")
