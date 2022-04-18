"""Functions and routines to read the stardust database and return what we want."""

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


MODULE_PATH = Path(__file__).parent


class StarDust:
    def __init__(self, fname: str = "PGD_SiC_2021-01-10.csv"):
        """Initialize the stardust class.

        Load the database into self.db and self._db as a backup

        :param fname: file name of csv file for database, default to most recent csv
            file in data folder. File must be in the data folder.
        """
        filepath = MODULE_PATH.joinpath(f"data/{fname}")
        self.db = pd.read_csv(filepath, index_col=0)
        self._db = self.db.copy(deep=True)

    def filter_value(
        self, value: float, iso1: str, iso2: str, comparator: str, err=False
    ):
        """Filter an isotope ratio (iso1 / iso2) for a given value.

        Will filter the database such that
        isotope_entry comparator value
        is True for all values.

        :param value: Value to compare with
        :type value: float
        :param iso1: Nominator isotope
        :type iso1: str
        :param iso2: Denominator isotope
        :type iso2: str
        :param comparator: Mathematical comparator to select for
        :type comparator: str
        :param err: Is the filter taking place on errors?
        :type err: bool

        :raise ValueError: Comparator is invalid

        Example to filter d(Si-29/Si-28) > 0.1, all others are out:
            >>> from stardustlib import StarDust
            >>> sd = StarDust()
            >>> sd.filter_value(0.1, "Si-29", "Si-28", ">")
        """
        hdr = self.header_ratio(iso1, iso2)[0]

        if err:
            hdr = f"err[{hdr}]"

        comp_dict = {
            "<": "<",
            ">": ">",
            "<=": "<=",
            "=<": "<=",
            ">=": ">=",
            "=>": ">=",
            "=": "==",
        }

        if comparator not in comp_dict.keys():
            raise ValueError(f"Comparator {comparator} is not valid.")

        # evaluate
        self.db = self.db[eval(f"self.db[hdr] {comp_dict[comparator]} {value}")]

    def filter_type(self, grain_type):
        """Filter grain database by grain type.

        :param grain_type: Grain type.
        :type grain_type: str, List[str]
        """
        if isinstance(grain_type, str):
            grain_type = [grain_type]

        self.db = self.db[self.db["PGD Type"].isin(grain_type)]

    def header_ratio(self, iso1: str, iso2: str) -> Tuple[str, bool]:
        """Check if isotope ratio is available and return it plus additional info.

        :param iso1: Nominator isotope, in format "Si-30"
        :type iso1: str
        :param iso2: Denominator isotope, in format "Si-28"
        :type iso2: str

        :return: name of ratio if exists or "none", Ratio is delta (bool)
        :rtype: Tuple[str, bool]
        """
        header = list(self.db.columns.values)

        isos = (create_db_iso(iso1), create_db_iso(iso2))

        # test delta
        hdr_ratio = f"{isos[0]}/{isos[1]}"
        hdr_delta = f"d({hdr_ratio})"
        if hdr_delta in header:
            delta = True
            hdr = hdr_delta
        elif hdr_ratio in header:
            delta = False
            hdr = hdr_ratio
        else:
            return "none", False

        return hdr, delta

    def reset(self):
        """Reset the database."""
        self.db = self._db.copy(deep=True)

    def return_ratios(
        self, isos1: Tuple[str, str], isos2: Tuple[str, str]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Grab ratios to plot after all the filtering was done.

        Fixme: Will always return values and errors, I think all data have values
            and errors
        Fixme: Currently if no errors reported, the whole datapoint is rejected
            with the dropna...

        :param isos1: Isotopes for first axis, as ratio, e.g., ("Si-29", "Si-28")
        :type isos1: Tuple[str, str]
        :param isos2: Isotopes for first axis, as ratio, e.g., ("Si-30", "Si-28")
        :type isos2: Tuple[str, str]

        :return: xdata, ydata, xerr, yerr
        :rtype: Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
        """
        hdr_x = self.header_ratio(isos1[0], isos1[1])[0]
        hdr_y = self.header_ratio(isos2[0], isos2[1])[0]
        hdr_x_err = f"err[{hdr_x}]"
        hdr_y_err = f"err[{hdr_y}]"

        df = self.db[[hdr_x, hdr_y, hdr_x_err, hdr_y_err]].copy()
        df.dropna(inplace=True)
        return (
            df[hdr_x].to_numpy(),
            df[hdr_y].to_numpy(),
            df[hdr_x_err].to_numpy(),
            df[hdr_y_err].to_numpy(),
        )


def create_db_iso(iso: str) -> str:
    """Create isotope name in database style.

    :param iso: Isotope name, class style, e.g., "Si-28"
    :type iso: str

    :return: Isotope name in database style, e.g., "28Si"
    :rtype: str
    """
    iso_split = iso.split("-")
    return iso_split[1] + iso_split[0]


if __name__ == "__main__":
    a = StarDust()
    a.filter_type("M")
    # a.filter_value(10.0, "Si-29", "Si-28", comparator="<=", err=True)
    # a.filter_value(10.0, "Si-30", "Si-28", comparator="<=", err=True)
    # print(a.return_ratios(("Si-30", "Si-28"), ("Si-29", "Si-28")))