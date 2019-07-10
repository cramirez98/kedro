# Copyright 2018-2019 QuantumBlack Visual Analytics Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
# NONINFRINGEMENT. IN NO EVENT WILL THE LICENSOR OR OTHER CONTRIBUTORS
# BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF, OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# The QuantumBlack Visual Analytics Limited ("QuantumBlack") name and logo
# (either separately or in combination, "QuantumBlack Trademarks") are
# trademarks of QuantumBlack. The License does not grant you any right or
# license to the QuantumBlack Trademarks. You may not use the QuantumBlack
# Trademarks or any confusingly similar mark as a trademark for your product,
#     or use the QuantumBlack Trademarks in any other manner that might cause
# confusion in the marketplace, including but not limited to in advertising,
# on websites, or on software.
#
# See the License for the specific language governing permissions and
# limitations under the License.

"""``HDFLocalDataSet`` loads and saves data to a local hdf file. The
underlying functionality is supported by pandas, so it supports all
allowed pandas options for loading and saving hdf files.
"""
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from pandas.io.pytables import HDFStore

from kedro.io.core import AbstractVersionedDataSet, DataSetError, Version


class HDFLocalDataSet(AbstractVersionedDataSet):
    """``HDFLocalDataSet`` loads and saves data to a local hdf file. The
    underlying functionality is supported by pandas, so it supports all
    allowed pandas options for loading and saving hdf files.

    Example:
    ::

        >>> from kedro.io import HDFLocalDataSet
        >>> import pandas as pd
        >>>
        >>> data = pd.DataFrame({'col1': [1, 2], 'col2': [4, 5],
        >>>                      'col3': [5, 6]})
        >>> data_set = HDFLocalDataSet(filepath="test.hdf",
        >>>                            key="test_hdf_key",
        >>>                            load_args=None,
        >>>                            save_args=None)
        >>> data_set.save(data)
        >>> reloaded = data_set.load()
        >>>
        >>> assert data.equals(reloaded)

    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        filepath: str,
        key: str,
        load_args: Dict[str, Any] = None,
        save_args: Dict[str, Any] = None,
        version: Version = None,
    ) -> None:
        """Creates a new instance of ``HDFLocalDataSet`` pointing to a concrete
        filepath.

        Args:
            filepath: Path to an hdf file.
            key: Identifier to the group in the HDF store.
            load_args: Pandas options for loading hdf files.
                Here you can find all available arguments:
                https://pandas.pydata.org/pandas-docs/stable/generated/pandas.read_hdf.html
                All defaults are preserved.
            save_args: Pandas options for saving hdf files.
                Here you can find all available arguments:
                https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.to_hdf.html
                All defaults are preserved.
            version: If specified, should be an instance of
                ``kedro.io.core.Version``. If its ``load`` attribute is
                None, the latest version will be loaded. If its ``save``
                attribute is None, save version will be autogenerated.

        """
        super().__init__(Path(filepath), version)
        default_load_args = {}
        default_save_args = {}
        self._key = key
        self._load_args = (
            {**default_load_args, **load_args}
            if load_args is not None
            else default_load_args
        )
        self._save_args = (
            {**default_load_args, **save_args}
            if save_args is not None
            else default_save_args
        )

    def _load(self) -> pd.DataFrame:
        load_path = Path(self._get_load_path())
        return pd.read_hdf(load_path, key=self._key, **self._load_args)

    def _save(self, data: pd.DataFrame) -> None:
        save_path = Path(self._get_save_path())
        save_path.parent.mkdir(parents=True, exist_ok=True)
        data.to_hdf(str(save_path), key=self._key, **self._save_args)

        load_path = Path(self._get_load_path())
        self._check_paths_consistency(load_path.absolute(), save_path.absolute())

    def _describe(self) -> Dict[str, Any]:
        return dict(
            filepath=self._filepath,
            key=self._key,
            load_args=self._load_args,
            save_args=self._save_args,
            version=self._version,
        )

    def _exists(self) -> bool:
        try:
            path = self._get_load_path()
        except DataSetError:
            return False
        if Path(path).is_file():
            with HDFStore(Path(path), mode="r") as hdfstore:
                key_with_slash = (
                    self._key if self._key.startswith("/") else "/" + self._key
                )
                if key_with_slash in hdfstore.keys():
                    return True
        return False
