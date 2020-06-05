"""
Just some utility functions used by notebooks and other scripts
"""

def str_to_array(string_numpy):
    """formatting : Conversion of String List to List

    Args:
        string_numpy (str)
    Returns:
        l (list): list of values
    """
    list_values = string_numpy.split(", ")
    list_values[0] = list_values[0][2:]
    list_values[-1] = list_values[-1][:-2]
    return list_values