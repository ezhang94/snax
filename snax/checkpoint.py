import dill as pickle
from pathlib import Path
from typing import TypeVar, Any, List, Optional, Tuple, Union
import jax

PyTreeDef = Any

Data = TypeVar('Data')

def save_checkpoint(
        data: Any,
        step: int,
        checkpoint_dir: str,
        num_checkpoints_to_keep: int = 3,
        name_prefix: str = "checkpoint",
        step_format: str = "{step:08d}",
        filetype: str = ".chk") -> None:
  existing_checkpoints = get_checkpoints(
          checkpoint_dir,
          name_prefix=name_prefix,
          filetype=filetype)
  checkpoint_steps = [step_from_path(f) for f in existing_checkpoints]
  assert len(checkpoint_steps) <= num_checkpoints_to_keep, "Too many checkpoints saved."
  assert len(checkpoint_steps) == len(set(checkpoint_steps)), "Non-unique checkpoint step."
  assert all([step > s for s in checkpoint_steps]), "Attempting to write earlier checkpoint."
  if len(checkpoint_steps) == num_checkpoints_to_keep:
    to_remove = checkpoint_steps.index(min(checkpoint_steps))
    existing_checkpoints[to_remove].unlink()
  new_name = name_prefix + "_" + step_format.format(step=step) + filetype
  new_path = Path(checkpoint_dir) / new_name
  save_checkpoint_to_path(data, step, new_path)

def get_checkpoints(
        checkpoint_dir: str,
        name_prefix: str = "checkpoint",
        filetype: str = ".chk") -> List[Path]:
  checkpoint_glob = name_prefix + '*' + filetype
  checkpoint_paths = Path(checkpoint_dir).glob(checkpoint_glob)
  return list(checkpoint_paths)

def step_from_path(path: Path) -> int:
  return int(path.stem.split("_")[1])

def get_latest_checkpoint_path(
        checkpoint_dir: str,
        name_prefix: str = "checkpoint",
        filetype: str = ".chk") -> Optional[Path]:
  paths = get_checkpoints(checkpoint_dir, name_prefix=name_prefix, filetype=filetype)
  if len(paths) == 0:
    return None
  steps = [step_from_path(x) for x in paths]
  max_ind = steps.index(max(steps))
  return paths[max_ind]

def load_latest_checkpoint(
        checkpoint_dir: str,
        name_prefix: str = "checkpoint",
        filetype: str = ".chk") -> Union[Tuple[None, None], Tuple[Any, int]]:
  path = get_latest_checkpoint_path(checkpoint_dir, name_prefix=name_prefix, filetype=filetype)
  if path is None:
    return None, None
  return load_checkpoint_from_path(path)

def load_checkpoint_from_path(path: Path) -> Tuple[Any, int]:
  with path.open(mode='rb') as f:
    data, step = pickle.load(f)
  return data, step

def save_checkpoint_to_path(data: Any, step: int, path: Path) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open(mode='wb') as f:
    pickle.dump((data, step), f)

def load_latest_checkpoint_with_treedef(
        treedef: PyTreeDef,
        checkpoint_dir: str,
        name_prefix: str = "checkpoint",
        filetype: str = ".chk") -> Union[Tuple[None, None], Tuple[Any, int]]:
  path = get_latest_checkpoint_path(checkpoint_dir, name_prefix=name_prefix, filetype=filetype)
  if path is None:
    return None, None
  new_model, step = load_checkpoint_from_path(path)
  loaded_leaves, _ = jax.tree_util.tree_flatten(new_model)
  loaded_leaves = [jax.numpy.array(x) for x in loaded_leaves]
  restored_model = treedef.unflatten(loaded_leaves)
  return restored_model, step
