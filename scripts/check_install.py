"""Run from outside the checkout after installing a built wheel."""
from pathlib import Path
from warpalign import Aligner
from warpalign.diagnostics import studio_directory
r=Aligner().align('ACGT','ACGTT')
assert r.score==8 and r.cigar=='4=1D'
assert (studio_directory()/'index.html').is_file(), 'Wheel has no Studio bundle'
assert '_studio' in str(studio_directory()),'Expected packaged frontend'
print('Installed native engine and bundled Studio verified')
