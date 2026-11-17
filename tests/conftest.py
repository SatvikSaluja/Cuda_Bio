"""Never write test sequences into a user's real Studio workspace."""
import os
import tempfile
os.environ['WARPALIGN_DATA_DIR']=tempfile.mkdtemp(prefix='warpalign-test-data-')
