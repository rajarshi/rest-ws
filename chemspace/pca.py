## http://www.mail-archive.com/numpy-discussion@scipy.org/msg06758.html
import numpy

def pca(data, algorithm='eig'):
  """pca(data) -> mean, pcs, norm_pcs, variances, positions, norm_positions
  Perform Principal Components Analysis on a set of n data points in k
  dimensions. The data array must be of shape (n, k).
  This function returns the mean data point, the principal components (of
  shape (p, k), where p is the number pf principal components: p=min(n,k)),
  the normalized principal components, where each component is normalized by
  the data's standard deviation along that component (shape (p, k)), the
  variance each component represents (shape (p,)), the position of each data
  point along each component (shape (n, p)), and the position of each data
  point along each normalized component (shape (n, p)).
  
  The optional algorithm parameter can be either 'svd' to perform PCA with 
  the singular value decomposition, or 'eig' to use a symmetric eigenvalue
  decomposition. Empirically, eig is faster on the datasets I have tested.
  """
  
  data = numpy.asarray(data)
  mean = data.mean(axis = 0)
  centered = data - mean
  if algorithm=='eig':
    pcs, variances, stds, positions, norm_positions = _pca_eig(centered)  
  elif algorithm=='svd':
    pcs, variances, stds, positions, norm_positions = _pca_svd(centered)  
  else:
    raise RuntimeError('Algorithm %s not known.'%algorithm)
  norm_pcs = pcs * stds[:, numpy.newaxis]
  return mean, pcs, norm_pcs, variances, positions, norm_positions
  
def _pca_svd(data):
  u, s, vt = numpy.linalg.svd(data, full_matrices = 0)
  pcs = vt
  v = numpy.transpose(vt)
  data_count = len(data.flat)
  variances = s**2 / data_count
  root_data_count = numpy.sqrt(data_count)
  stds = s / root_data_count
  positions =  u * s
  norm_positions = u * root_data_count
  return pcs, variances, stds, positions, norm_positions

def _pca_eig(data):
  values, vectors = _symm_eig(data)
  pcs = vectors.transpose()
  variances = values / len(data.flat)
  stds = numpy.sqrt(variances)
  positions = numpy.dot(data.flat, vectors)
  err = numpy.seterr(divide='ignore', invalid='ignore')
  norm_positions = positions / stds
  numpy.seterr(**err)
  norm_positions[~numpy.isfinite(norm_positions)] = 0
  return pcs, variances, stds, positions, norm_positions

def _symm_eig(a):
  """Return the eigenvectors and eigenvalues of the symmetric matrix a'a. If
  a has more columns than rows, then that matrix will be rank-deficient,
  and the non-zero eigenvalues and eigenvectors can be more easily extracted
  from the matrix aa'.
  From the properties of the SVD:
    if a of shape (m,n) has SVD u*s*v', then:
      a'a = v*s's*v'
      aa' = u*ss'*u'
    let s_hat, an array of shape (m,n), be such that s * s_hat = I(m,m) 
    and s_hat * s = I(n,n). (Note that s_hat is just the elementwise 
    reciprocal of s, as s is zero except on the main diagonal.)
    
    Thus, we can solve for u or v in terms of the other:
      v = a'*u*s_hat'
      u = a*v*s_hat      
  """
  m, n = a.shape
  if m >= n:
    # just return the eigenvalues and eigenvectors of a'a
    vecs, vals = _eigh(numpy.dot(a.transpose(), a))
    vecs = numpy.where(vecs < 0, 0, vecs)
    return vecs, vals
  else:
    # figure out the eigenvalues and vectors based on aa', which is smaller
    sst_diag, u = _eigh(numpy.dot(a, a.transpose()))
    # in case due to numerical instabilities we have sst_diag < 0 anywhere, 
    # peg them to zero
    sst_diag = numpy.where(sst_diag < 0, 0, sst_diag)
    # now get the inverse square root of the diagonal, which will form the
    # main diagonal of s_hat
    err = numpy.seterr(divide='ignore', invalid='ignore')
    s_hat_diag = 1/numpy.sqrt(sst_diag)
    numpy.seterr(**err)
    s_hat_diag[~numpy.isfinite(s_hat_diag)] = 0
    # s_hat_diag is a list of length m, a'u is (n,m), so we can just use
    # numpy's broadcasting instead of matrix multiplication, and only create
    # the upper mxm block of a'u, since that's all we'll use anyway...
    v = numpy.dot(a.transpose(), u[:,:m]) * s_hat_diag
    return sst_diag, v

def _eigh(m):
  values, vectors = numpy.linalg.eigh(m)
  order = numpy.flipud(values.argsort())
  return values[order], vectors[:,order]
