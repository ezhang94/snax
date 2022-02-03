import jax
import jax.numpy as jnp
from chex import Array

def flip_first_n(x: Array, n: int) -> Array:
  xlen = x.shape[0]
  inds = jnp.arange(xlen - 1, stop=-1, step=-1)
  inds -= (xlen - n)
  return x[inds]

def register_pytree(data_class):
  flatten = lambda d: jax.util.unzip2(sorted(d.__dict__.items()))[::-1]
  unflatten = lambda keys, values: data_class(**dict(zip(keys, values)))
  try:
    jax.tree_util.register_pytree_node(
        nodetype=data_class, flatten_func=flatten, unflatten_func=unflatten)
  except ValueError:
    print("%s is already registered as JAX PyTree node.", data_class)
  return data_class

def identity_init(key, shape, dtype=jnp.float_):
  assert len(shape) == 2
  return jnp.eye(shape[0], M=shape[1], dtype=dtype)

def stack_identity_init(num_reps):

  def init(key, shape, dtype=jnp.float32):
    assert len(shape) == 2
    assert shape[1] % num_reps == 0
    ms = []
    for _ in range(num_reps):
      ms.append(jnp.eye(shape[0], M=shape[1]//num_reps, dtype=dtype))
    return jnp.concatenate(ms, axis=1)

  return init