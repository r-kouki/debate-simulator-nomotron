"""
Dual Model Manager - Manages two model instances with dynamic adapter loading.

Loads two instances of the base LLM (Pro and Con) to enable parallel generation
and independent adapter swapping for each stance.
"""

import torch
from pathlib import Path
from typing import Optional
from peft import PeftModel

from src.utils.model_loader import load_base_model, ADAPTERS_PATH


class DualModelManager:
    """
    Manages two model instances for Pro and Con debaters.
    
    Each instance can have its own domain adapter loaded dynamically.
    With 48GB VRAM, we can comfortably fit two 8B models in 4-bit quantization
    (~6GB each) plus adapters.
    """
    
    def __init__(self, device_map: str = "auto"):
        """
        Initialize dual model manager.
        
        Args:
            device_map: Device placement strategy ("auto", "cuda:0", "cuda:1", etc.)
        """
        self.device_map = device_map
        
        # Model instances (lazy loaded)
        self._model_pro = None
        self._model_con = None
        self._tokenizer_pro = None
        self._tokenizer_con = None
        
        # Track current adapters
        self.current_adapter_pro: Optional[str] = None
        self.current_adapter_con: Optional[str] = None
        
        # Base model references (before adapter)
        self._base_model_pro = None
        self._base_model_con = None
    
    def _load_model_instance(self, instance_name: str) -> tuple:
        """Load a single model instance."""
        print(f"Loading {instance_name} model instance...")
        model, tokenizer = load_base_model()
        
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1e9
            print(f"  → {instance_name} model loaded. VRAM used: {allocated:.2f} GB")
        
        return model, tokenizer
    
    @property
    def model_pro(self):
        """Lazy load Pro model."""
        if self._model_pro is None:
            self._model_pro, self._tokenizer_pro = self._load_model_instance("Pro")
            self._base_model_pro = self._model_pro
        return self._model_pro
    
    @property
    def model_con(self):
        """Lazy load Con model."""
        if self._model_con is None:
            self._model_con, self._tokenizer_con = self._load_model_instance("Con")
            self._base_model_con = self._model_con
        return self._model_con
    
    @property
    def tokenizer_pro(self):
        """Get Pro tokenizer (loads model if needed)."""
        if self._tokenizer_pro is None:
            _ = self.model_pro  # Trigger lazy load
        return self._tokenizer_pro
    
    @property
    def tokenizer_con(self):
        """Get Con tokenizer (loads model if needed)."""
        if self._tokenizer_con is None:
            _ = self.model_con  # Trigger lazy load
        return self._tokenizer_con
    
    def load_adapter(self, model_key: str, domain: str) -> bool:
        """
        Load a domain adapter onto the specified model.
        
        Args:
            model_key: "pro" or "con"
            domain: Domain name (education, medicine, ecology, technology, debate)
            
        Returns:
            True if adapter was loaded, False if not found (uses base model)
        """
        adapter_path = ADAPTERS_PATH / domain
        
        if not adapter_path.exists():
            print(f"⚠ No adapter found for '{domain}' at {adapter_path}, using base model")
            return False
        
        if model_key == "pro":
            return self._load_adapter_pro(domain, adapter_path)
        elif model_key == "con":
            return self._load_adapter_con(domain, adapter_path)
        else:
            raise ValueError(f"Invalid model_key: {model_key}. Use 'pro' or 'con'.")
    
    def _load_adapter_pro(self, domain: str, adapter_path: Path) -> bool:
        """Load adapter onto Pro model."""
        if self.current_adapter_pro == domain:
            print(f"  → Pro model already has '{domain}' adapter loaded")
            return True
        
        # Ensure model is loaded
        _ = self.model_pro
        
        # Unload previous adapter by reverting to base model
        if self.current_adapter_pro is not None:
            print(f"  → Unloading '{self.current_adapter_pro}' adapter from Pro model")
            if isinstance(self._model_pro, PeftModel):
                self._model_pro = self._base_model_pro
        
        # Load new adapter
        print(f"  → Loading '{domain}' adapter onto Pro model...")
        self._model_pro = PeftModel.from_pretrained(
            self._model_pro,
            adapter_path,
            is_trainable=False,
        )
        self.current_adapter_pro = domain
        print(f"  ✓ Pro model now using '{domain}' adapter")
        return True
    
    def _load_adapter_con(self, domain: str, adapter_path: Path) -> bool:
        """Load adapter onto Con model."""
        if self.current_adapter_con == domain:
            print(f"  → Con model already has '{domain}' adapter loaded")
            return True
        
        # Ensure model is loaded
        _ = self.model_con
        
        # Unload previous adapter
        if self.current_adapter_con is not None:
            print(f"  → Unloading '{self.current_adapter_con}' adapter from Con model")
            if isinstance(self._model_con, PeftModel):
                self._model_con = self._base_model_con
        
        # Load new adapter
        print(f"  → Loading '{domain}' adapter onto Con model...")
        self._model_con = PeftModel.from_pretrained(
            self._model_con,
            adapter_path,
            is_trainable=False,
        )
        self.current_adapter_con = domain
        print(f"  ✓ Con model now using '{domain}' adapter")
        return True
    
    def unload_adapters(self):
        """Unload all adapters, reverting to base models."""
        if self.current_adapter_pro and isinstance(self._model_pro, PeftModel):
            self._model_pro = self._base_model_pro
            self.current_adapter_pro = None
            print("  → Pro adapter unloaded")
        
        if self.current_adapter_con and isinstance(self._model_con, PeftModel):
            self._model_con = self._base_model_con
            self.current_adapter_con = None
            print("  → Con adapter unloaded")
    
    def generate_pro(
        self,
        prompt: str,
        max_tokens: int = 200,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """
        Generate response using Pro model.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum new tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            
        Returns:
            Generated text (without the prompt)
        """
        return self._generate(
            self.model_pro,
            self.tokenizer_pro,
            prompt,
            max_tokens,
            temperature,
            top_p,
        )
    
    def generate_con(
        self,
        prompt: str,
        max_tokens: int = 200,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """Generate response using Con model."""
        return self._generate(
            self.model_con,
            self.tokenizer_con,
            prompt,
            max_tokens,
            temperature,
            top_p,
        )
    
    def _generate(
        self,
        model,
        tokenizer,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
    ) -> str:
        """Internal generation method."""
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )
        
        # Decode only the new tokens
        input_length = inputs["input_ids"].shape[1]
        generated_tokens = outputs[0][input_length:]
        response = tokenizer.decode(generated_tokens, skip_special_tokens=True)
        
        return response.strip()
    
    def get_memory_stats(self) -> dict:
        """Get current GPU memory statistics."""
        if not torch.cuda.is_available():
            return {"gpu_available": False}
        
        stats = {
            "gpu_available": True,
            "gpu_count": torch.cuda.device_count(),
            "devices": [],
        }
        
        for i in range(torch.cuda.device_count()):
            stats["devices"].append({
                "device": i,
                "name": torch.cuda.get_device_name(i),
                "allocated_gb": torch.cuda.memory_allocated(i) / 1e9,
                "reserved_gb": torch.cuda.memory_reserved(i) / 1e9,
                "total_gb": torch.cuda.get_device_properties(i).total_memory / 1e9,
            })
        
        return stats
    
    def __repr__(self) -> str:
        pro_status = f"adapter={self.current_adapter_pro}" if self.current_adapter_pro else "base"
        con_status = f"adapter={self.current_adapter_con}" if self.current_adapter_con else "base"
        return f"DualModelManager(pro={pro_status}, con={con_status})"
