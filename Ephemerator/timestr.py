"""Collection of (currently unused) timestring methods"""
import re
import datetime

conv_dict = {
    'Y': 'years',
    'M': 'months',
    'w': 'weeks',
    'd': 'days',
    'h': 'hours',
    'm': 'minutes',
    's': 'seconds'
}

PAT = r'[0-9]+[s|m|h|d|w|M|Y]{1}'
#pat = r'[0-9]+[s|m|h|d|w]{1}'


def timestr_to_dict(timestring):
    """
    Convert a string of the form "[0-9]*Y[0-9]*M[0-9]*w[0-9]*d[0-9]*h[0-9]*m[0-9]*s"
    to a dictionary of the form {"weeks": w + (4 * M) + (52 * Y), "days": d, "hours": h, "minutes": m, "seconds": s}

    Since python datetime.timedelta does not support months or years, we need to do some math to convert those parts to weeks in the output.

    Parameters
    ----------
    timestring : str
        A string of the form "[0-9]*Y[0-9]*M[0-9]*w[0-9]*d[0-9]*h[0-9]*m[0-9]*s".
        If you want to exclude a time unit, do not include it in the string (0 will work as well).

    Returns
    -------
    dict
        A dictionary of the form {"weeks": w + (4 * M) + (52 * Y), "days": d, "hours": h, "minutes": m, "seconds": s}.

    See Also
    --------
    timestr_to_seconds: convert the dict output from this function to seconds.

    Examples
    --------
    >>> timestr_to_dict("1Y2M3w4d5h6m7s")
    {'weeks': 68, 'days': 4, 'hours': 5, 'minutes': 6, 'seconds': 7}
    >>> timestr_to_dict("1Y2d4m")
    {'weeks': 52, 'days': 2,'minutes': 4}
    >>> timestr_to_dict("5m")
    {'minutes': 5}
    """
    timestr_dict = {conv_dict[p[-1]]: int(p[:-1])
                   for p in re.findall(PAT, timestring)}
    months_to_weeks = timestr_dict.get('months', 0) * 4
    years_to_weeks = timestr_dict.get('years', 0) * 52
    timestr_dict['weeks'] = months_to_weeks + \
        years_to_weeks + timestr_dict.get('weeks', 0)
    timestr_dict.pop('months', None)
    timestr_dict.pop('years', None)
    return timestr_dict


def timestr_to_seconds(timestring):
    """
    Converts a dict from timestr_to_dict into seconds.

    Parameters
    ----------
    timestring : str
        A string of the form "[0-9]*Y[0-9]*M[0-9]*w[0-9]*d[0-9]*h[0-9]*m[0-9]*s".
        If you want to exclude a time unit, do not include it in the string (0 will work as well).

    Returns
    -------
    int
        The number of seconds the input string represents.

    See Also
    --------
    timestr_to_dict: convert a string of the form "[0-9]*Y[0-9]*M[0-9]*w[0-9]*d[0-9]*h[0-9]*m[0-9]*s"
        to a dictionary of the form {"weeks": w + (4 * M) + (52 * Y), "days": d, "hours": h, "minutes": m, "seconds": s}.

    Examples
    --------
    >>> timestr_to_seconds("2d4h3m2s")
    187382
    """
    return datetime.timedelta(**timestr_to_dict(timestring)).total_seconds()
