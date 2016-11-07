"""A function to calculate the age of a person at a given timepoint."""

# Python imports.
import datetime


def main(born, comparison=None, isFraction=False):
    """Calculate a person's age at a given timepoint.

    :param born:        The date when the person was born.
    :type born:         datetime.datetime
    :param comparison:  The date to compare the birthday against (or today's date if no date is supplied).
    :type comparison:   datetime.datetime
    :param isFraction:  Whether the age should be returned as a fractional year (e.g. 35.3) or not (e.g. 35). Rounding
                            to the nearest year is always performed down.
    :type isFraction:   bool

    """

    # Get date to compare against if needed.
    if not comparison:
        comparison = datetime.datetime.today()

    # Determine if their birthday would have occurred already in the year that comparison occurs in. For example, if the
    # person was born on March 5th 1970 and the comparison date is May 12th 2010, then there birthday would already have
    # occurred. However, if the comparison is January 12th 2010, then their birthday would not already have occurred.
    birthdayOccurred = (born.month, born.day) < (comparison.month, comparison.day)

    # Get the integer number of years.
    yearsOld = comparison.year - born.year - (not birthdayOccurred)

    # Determine days until the person's next birthday.
    if birthdayOccurred:
        # The person's birthday has occurred in the comparison year, so use the year after it to determine their next
        # birthday.
        try:
            nextBirthday = born.replace(year=comparison.year + 1)
        except ValueError:
            # The patient was born on February 29th and the current year was a leap year. Therefore their
            # birthday does not 'exist' in the next year. Instead, pretend their birthday in the next year is March 1st.
            nextBirthday = born.replace(year=comparison.year + 1, month=3, day=1)
    else:
        # The person's birthday has not occurred in the comparison year, so use the comparison year to determine their
        # next birthday.
        try:
            nextBirthday = born.replace(year=comparison.year)
        except ValueError:
            # The patient was born on February 29th and the current year was a leap year. Therefore their
            # birthday does not 'exist' in the next year. Instead, pretend their birthday in the next year is March 1st.
            nextBirthday = born.replace(year=comparison.year, month=3, day=1)
    daysUntilBirthday = nextBirthday - comparison

    # Return the person's age.
    meanSecondsInYear = 365.25 * 24 * 60 * 60
    if isFraction:
        return yearsOld + ((meanSecondsInYear - daysUntilBirthday.total_seconds()) / meanSecondsInYear)
    else:
        return yearsOld
