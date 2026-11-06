"""Isolated diffusion worker. The web application's environment stays lightweight."""
import argparse
import json
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def generate(job,pipe=None):
    import torch
    from diffusers import StableDiffusionPipeline, StableDiffusionControlNetPipeline, ControlNetModel, DPMSolverMultistepScheduler
    from PIL import ImageStat
    torch.set_num_threads(4)

    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable in the media environment')
    start=time.monotonic()
    precision=job.get('precision','float32')
    if pipe is not None:
        precision='float32' if pipe.unet.dtype==torch.float32 else 'float16'
    dtype=torch.float16 if precision=='float16' else torch.float32
    # This GTX 1660 produced non-finite half-precision latents. Float32 with
    # layer-level offload proved both stable and faster than whole-model offload.
    if pipe is None:
        extras={}
        pipeline_class=StableDiffusionPipeline
        if job.get('control_image'):
            extras['controlnet']=ControlNetModel.from_pretrained(str(ROOT/'models/controlnet-canny'),
                variant='fp16',torch_dtype=dtype,local_files_only=True,use_safetensors=True)
            pipeline_class=StableDiffusionControlNetPipeline
        pipe=pipeline_class.from_pretrained(
            str(ROOT/'models/dreamshaper-8'),torch_dtype=dtype,
            variant='fp16',local_files_only=True,use_safetensors=True,**extras)
        pipe.scheduler=DPMSolverMultistepScheduler.from_config(pipe.scheduler.config,
            algorithm_type='dpmsolver++',solver_order=2,use_karras_sigmas=True)
        if dtype==torch.float32: pipe.enable_sequential_cpu_offload()
        else: pipe.enable_model_cpu_offload()
        pipe.enable_attention_slicing()
        pipe.enable_vae_slicing()
    def check_step(current,step,timestep,values):
        if step%5==0 and not torch.isfinite(values['latents']).all():
            raise FloatingPointError('Non-finite diffusion latents')
        return values
    for attempt in range(2):
        generator=torch.Generator(device='cpu').manual_seed(job['seed'])
        try:
            extras={}
            if job.get('control_image'):
                import cv2
                import numpy as np
                from PIL import Image
                edges=cv2.Canny(np.array(Image.open(job['control_image']).convert('RGB')),100,200)
                extras={'image':Image.fromarray(np.repeat(edges[:,:,None],3,axis=2)),
                        'controlnet_conditioning_scale':job.get('control_strength',.9),'control_guidance_end':.9}
            result=pipe(job['prompt'],negative_prompt=job['negative_prompt'],
                width=job.get('width',512),height=job.get('height',704),output_type='latent',
                num_inference_steps=job.get('steps',28),guidance_scale=job.get('guidance',7.5),
                generator=generator,callback_on_step_end=check_step,**extras)
            break
        except FloatingPointError:
            if attempt or precision=='float32': raise
            print('Half-precision arithmetic failed; retrying float32 with layer-by-layer CPU offload.',flush=True)
            pipe.remove_all_hooks()
            pipe.to('cpu',torch.float32)
            pipe.enable_sequential_cpu_offload()
            precision='float32 sequential offload'
    # The GTX 1660 family can overflow in half-precision VAE decoding. Decode
    # and classify in float32 while retaining the memory-saving UNet settings.
    pipe.vae.to(dtype=torch.float32)
    pipe.safety_checker.to(dtype=torch.float32)
    with torch.inference_mode():
        decoded=pipe.vae.decode(result.images.float()/pipe.vae.config.scaling_factor,return_dict=False)[0]
        if not torch.isfinite(decoded).all(): raise FloatingPointError('Non-finite VAE output')
        output=Path(job['output']); output.parent.mkdir(parents=True,exist_ok=True)
        # Private diagnostic only: rejected candidates are never API deliverables.
        candidate=pipe.image_processor.postprocess(decoded,output_type='pil')[0].convert('RGB')
        candidate.save(output.with_name(output.stem+'-candidate.png'))
        decoded,flags=pipe.run_safety_checker(decoded,pipe._execution_device,torch.float32)
    if flags and any(flags):
        raise RuntimeError('The image model rejected the generated image; revise the brief.')
    image=pipe.image_processor.postprocess(decoded,output_type='pil')[0].convert('RGB')
    pipe.maybe_free_model_hooks()
    if sum(ImageStat.Stat(image).stddev)<12:
        raise RuntimeError('Diffusion produced a blank/low-information image')
    image.save(output)
    report={**job,'engine':'diffusion','model':'Lykon/dreamshaper-8',
            'revision':'a7e52b98680b1ba8ff7bce97c7f9f2e2e5337917',
            'device':torch.cuda.get_device_name(),'precision':precision+'; layer-level CPU offload',
            'seconds':round(time.monotonic()-start,2),
            'peak_vram_mib':round(torch.cuda.max_memory_allocated()/1024**2)}
    if job.get('control_image'):
        report['composition_model']='lllyasviel/control_v11p_sd15_canny'
        report['composition_revision']='115a470d547982438f70198e353a921996e2e819'
    output.with_suffix('.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps({'saved':str(output),'seconds':report['seconds'],'peak_vram_mib':report['peak_vram_mib']}),flush=True)
    return pipe


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('job',type=Path,nargs='+')
    args=parser.parse_args()
    pipeline=None
    for job_path in args.job:
        pipeline=generate(json.loads(job_path.read_text(encoding='utf8')),pipeline)
