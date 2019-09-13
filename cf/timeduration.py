from operator import __add__, __sub__

from ast         import literal_eval
from collections import namedtuple
from datetime    import datetime
from functools   import partial as functools_partial

import numpy
from numpy import array     as numpy_array
from numpy import size      as numpy_size
from numpy import vectorize as numpy_vectorize

from .cfdatetime import elements #Datetime
from .cfdatetime import dt as cf_dt
from .functions  import equals
from .functions  import _DEPRECATION_ERROR_KWARGS
from .functions  import inspect as cf_inspect
from .units      import Units

from .data.data import Data


# Define some useful units
_calendar_years  = Units('calendar_years')
_calendar_months = Units('calendar_months')
_days            = Units('days')
_hours           = Units('hours')
_minutes         = Units('minutes')
_seconds         = Units('seconds')

# Define some useful constants
_one_year   = Data(1, 'calendar_years')
_one_day    = Data(1, 'day')
_one_hour   = Data(1, 'hour')
_one_minute = Data(1, 'minute')

# Default month lengths in days
_default_month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

_default_calendar = 'gregorian'

Offset = namedtuple('offset', ('year', 'month', 'day', 'hour',
                               'minute', 'second', 'microsecond'))


class TimeDuration:
    '''A duration of time.

The duration of time is a number of either calendar years, calender
months, days, hours, minutes or seconds.

A calendar year (or month) is an arbitrary year (or month) in an
arbitrary calendar. A calendar is as part of the time duration, but
will be taken from the context in which the time duration instance is
being used. For example, a calendar may be specified when creating
time intervals (see below for examples).

A default offset is specified that may be used by some applications to
temporally position the time duration. For example, setting
``cf.TimeDuration(1, 'calendar_month', day=16, hour=12)`` will define
a duration of one calendar month which, by default, starts at 12:00 on
the 16th of the month. Note that the offset

**Changing the units**

The time duration's units may be changed in place by assigning
equivalent units to the `~cf.TimeDuration.Units` attribute:

>>> t = cf.TimeDuration(1, 'day')
>>> t
<CF TimeDuration: 1 day (from Y-M-D 00:00:00)>
>>> t.Units = 's' 
>>> t
<CF TimeDuration: 86400.0 s (from Y-M-D h:m:s)> 
>>> t.Units = cf.Units('minutes')
>>> t
<CF TimeDuration: 1440.0 minutes (from Y-M-D h:m:00)> 
>>> t.Units = 'calendar_months'
ValueError: Can't set units to non-equivalent units

**Creating time intervals**

A time interval of exactly the time duration, starting or ending at a
particular date-time, may be produced with the `interval` method. If
elements of the start or end date-time are not specified, then default
values are taken from the `!year`, `!month`, `!day`, `!hour`,
`!minute`, and `!second` attributes of the time duration instance:

>>> t = cf.TimeDuration(6, 'calendar_months')
>>> t
<CF TimeDuration: 6 calendar_months (from Y-M-01 00:00:00)>
>>> t.interval(1999, 12)
(<CF Datetime: 1999-12-01 00:00:00>, <CF Datetime: 2000-06-01 00:00:00>)
>>> t = cf.TimeDuration(5, 'days', hour=6)
>>> t
<CF TimeDuration: 5 days (from Y-M-D 06:00:00)>
>>> t.interval(2004, 3, 2, end=True)
(datetime.datetime(2004, 2, 26, 6, 0), <CF Datetime: 2004-03-02 06:00:00>)
>>> t.interval(2004, 3, 2, end=True, calendar='noleap')
(<CF Datetime: 2004-02-25 06:00:00>, <CF Datetime: 2004-03-02 06:00:00>)
>>> t.interval(2004, 3, 2, end=True, calendar='360_day')
(<CF Datetime: 2004-02-27 06:00:00>, <CF Datetime: 2004-03-02 06:00:00>)
>>> t.interval(2004, 3, 2, end=True, calendar='360_day', iso='start and duration')
'2004-02-27 06:00:00/P5D'


**Comparison operations**

Comparison operations are defined for `cf.TimeDuration` objects,
``cf.Data` objects, `numpy` arrays and numbers:

>>> cf.TimeDuration(2, 'calendar_years') > cf.TimeDuration(1, 'calendar_years')
True
>>> cf.TimeDuration(2, 'calendar_years') < cf.TimeDuration(25, 'calendar_months')
True
>>> cf.TimeDuration(2, 'hours') <= cf.TimeDuration(1, 'days')
True
>>> cf.TimeDuration(2, 'hours') == cf.TimeDuration(1/12.0, 'days')
True
>>> cf.TimeDuration(2, 'days') == cf.TimeDuration(48, 'hours')
True

>>> cf.TimeDuration(2, 'hours') <= 2
True
>>> 30.5 != cf.TimeDuration(2, 'days')
True

>>> cf.TimeDuration(2, 'calendar_years') > numpy.array(1.5)
True
>>> type(cf.TimeDuration(2, 'calendar_years') > numpy.array(1.5))
numpy.bool_
>>> cf.TimeDuration(2, 'calendar_years') > numpy.array([1.5])
array([ True], dtype=bool)
>>> numpy.array([[1, 12]]) > cf.TimeDuration(2, 'calendar_months')
array([[False,  True]], dtype=bool)

>>> cf.TimeDuration(2, 'days') == cf.Data(2)
<CF Data: True>
>>> cf.TimeDuration(2, 'days') == cf.Data([2.], 'days')
<CF Data: [True]>
>>> cf.Data([[60]], 'seconds') < cf.TimeDuration(2, 'days')
<CF Data: [[True]]>
>>> cf.Data([1, 12], 'calendar_months') < cf.TimeDuration(6, 'calendar_months')
<CF Data: [True, False]>


**Arithmetic operations**

Arithmetic operations are defined for `cf.TimeDuration` objects,
date-time-like objects (such as `cf.Datetime`, `datetime.datetime`,
etc.), ``cf.Data` objects, `numpy` arrays and numbers:

>>> cf.TimeDuration(64, 'days') + cf.TimeDuration(28, 'days')
<CF TimeDuration: P92D (Y-M-D 00:00:00)>
>>> cf.TimeDuration(64, 'days') + cf.TimeDuration(12, 'hours')
<CF TimeDuration: P65.0D (Y-M-D 00:00:00)>
>>> cf.TimeDuration(64, 'days') + cf.TimeDuration(24, 'hours')
<CF TimeDuration: P64.5D (Y-M-D 00:00:00)>
>>> cf.TimeDuration(64, 'calendar_years') + cf.TimeDuration(21, 'calendar_months')
<CF TimeDuration: P65.75Y (Y-01-01 00:00:00)>

>>> cf.TimeDuration(30, 'days') + 2
<CF TimeDuration: P32D (Y-M-D 00:00:00)>
>>> 4.5 + cf.TimeDuration(30, 'days')
<CF TimeDuration: P34.5D (Y-M-D 00:00:00)>
>>> cf.TimeDuration(64, 'calendar_years') - 2.5
<CF TimeDuration: P61.5Y (Y-01-01 00:00:00)>

 TODO : update repr output in examples

>>> cf.TimeDuration(36, 'hours') / numpy.array(8)
<CF TimeDuration: 4.5 hours (from Y-M-D h:00:00)>
>>> cf.TimeDuration(36, 'hours') / numpy.array(8.0)
<CF TimeDuration: 4.5 hours (from Y-M-D h:00:00)>
>>> cf.TimeDuration(36, 'hours') // numpy.array(8.0)
<CF TimeDuration: 4.0 hours (from Y-M-D h:00:00)>
>>> cf.TimeDuration(36, 'calendar_months') * cf.Data([[2.25]])
<CF TimeDuration: 81.0 calendar_months (from Y-M-01 00:00:00)>
>>> cf.TimeDuration(36, 'calendar_months') // cf.Data([0.825], '10')
<CF TimeDuration: 4.3 calendar_months (from Y-M-01 00:00:00)>
>>> cf.TimeDuration(36, 'calendar_months') % 10
<CF Data: 6 calendar_months>
>>> cf.TimeDuration(36, 'calendar_months') % cf.Data(1, 'calendar_year')
<CF Data: 0.0 calendar_months>
>>> cf.TimeDuration(36, 'calendar_months') % cf.Data(2, 'calendar_year')
<CF Data: 12.0 calendar_months>

The in place operators (``+=``, ``//=``, etc.) are supported in a
similar manner.

**Attributes**

===========  =========================================================
Attribute    Description
===========  =========================================================
`!duration`  The length of the time duration in a `cf.Data` object
             with units.
`!year`      The default year for time interval creation.
`!month`     The default month for time interval creation.
`!day`       The default day for time interval creation.
`!hour`      The default hour for time interval creation.
`!minute`    The default minute for time interval creation.
`!second`    The default second for time interval creation.
===========  =========================================================


**Constructors**

For convenience, the following functions may also be used to create
time duration objects:

========  ============================================================
Function  Description
========  ============================================================
`cf.Y`    Create a time duration of calendar years.
`cf.M`    Create a time duration of calendar months.
`cf.D`    Create a time duration of days.
`cf.h`    Create a time duration of hours.
`cf.m`    Create a time duration of minutes.
`cf.s`    Create a time duration of seconds.
========  ============================================================

.. seealso:: `cf.dt`, `cf.Data`, `cf.Datetime`

.. versionadded:: 1.0

    '''
    def __init__(self, duration, units=None, month=1, day=1, hour=0,
                 minute=0, second=0): 
        '''**Initialization**

:Parameters:

    duration: data-like
        The length of the time duration.

        A data-like object is any object containing array-like or
        scalar data which could be used to create a `cf.Data` object.
    
        *Parameter example:*
          Instances, ``x``, of following types are all examples of
          data-like objects (because ``cf.Data(x)`` creates a valid
          `cf.Data` object), `int`, `float`, `str`, `tuple`, `list`,
          `numpy.ndarray`, `cf.Data`, `cf.Coordinate`, `cf.Field`.

    units: `str` or `cf.Units`, optional
        The units of the time duration. Required if, and only if,
        *duration* is not a `cf.Data` object which already contains
        the units. Units must be one of calendar years, calendar
        months, days, hours, minutes or seconds.

        *Parameter example:*
          ``units='calendar_months'``

        *Parameter example:*
          ``units='days'``

        *Parameter example:*
          ``units=cf.Units('calendar_years')``

     month, day, hour, minute, second: `int` or `None`, optional         
        The offset used when creating, with the `bounds` method, a
        time interval containing a given date-time. Only the offset
        elements for units smaller that of the time duration are used.

        *Parameter example:*
          >>> cf.TimeDuration(1, 'calendar_month').bounds(cf.dt('2000-1-8'))
          (<CF Datetime: 2000-01-01 00:00:00>, <CF Datetime: 2000-02-01 00:00:00>)
          >>> cf.TimeDuration(1, 'calendar_month', day=15).bounds(cf.dt('2000-1-8'))
          (<CF Datetime: 1999-12-15 00:00:00>, <CF Datetime: 2000-01-15 00:00:00>)
          >>> cf.TimeDuration(1, 'calendar_month', month=4, day=30).bounds(cf.dt('2000-1-8'))
          (<CF Datetime: 1999-12-30 00:00:00>, <CF Datetime: 2000-01-30 00:00:00>)

**Examples:**

>>> t = cf.TimeDuration(cf.Data(3 , 'calendar_years'))
>>> t = cf.TimeDuration(cf.Data(12 , 'hours'))
>>> t = cf.TimeDuration(18 , 'calendar_months')
>>> t = cf.TimeDuration(30 , 'days')
>>> t = cf.TimeDuration(1 , 'day', hour=6)

        '''
        if units is not None:
            units = Units(units)
            self.duration = Data(abs(duration))
            if self.duration.Units.istime:
                self.duration.Units = units
            else:
                self.duration = Data(self.duration.array, units)
        else:
            self.duration = abs(Data.asdata(duration))
            units = self.duration.Units
            if not units.istime:
                raise ValueError("Bad units: {!r}".format(units))

        if not (units.iscalendartime or units.istime):
            raise ValueError(
                "Can't create {0} of {1}".format(self.__class__.__name__, self.duration))
            
        duration = self.duration

        offset = [None, month, day, hour, minute, second, 0]
        if units.equivalent(_calendar_years):
            if duration < _one_year:
                offset[1] = None
        else:
            offset[1] = None
            offset[2] = None 
            if units <= _hours and duration < _one_day:
                offset[3] = None
                if units <= _minutes and duration < _one_hour:
                    offset[4] = None
                    if units <= _seconds and duration < _one_minute:
                        offset[5] = None
        #--- End: if
        self.offset = Offset(*offset)

# TODO should offset be None for all "higher" units
        
        self._compound = False

        self._NotImplemented_RHS_Data_op = True
    #--- End: def

    def __abs__(self):
        '''x.__abs__() <==> abs(x)

    .. versionadded:: 1.4

        '''
        out = self.copy()
        out.duration = abs(self.duration)
        return out


    def __array__(self, *dtype):
        '''TODO
'''
        return self.duration.__array__(*dtype)


    def __data__(self):
        '''Returns a new reference to the `!duration` attribute.

        '''
        return self.duration


    def __deepcopy__(self, memo):
        '''Used if copy.deepcopy is called

        ''' 
        return self.copy()


    def __neg__(self):
        '''x.__neg__() <==> -x

    .. versionadded:: 1.4

        '''
        out = self.copy()
        out.duration *= -1
        return out


    def __bool__(self):
        '''Truth value testing and the built-in operation `bool`

    x.__bool__() <==> bool(x)

        '''
        return bool(self.duration)


    def __int__(self):
        '''x.__int__() <==> int(x)

        '''
        return int(self.duration)


    def __repr__(self):
        '''x.__repr__() <==> repr(x)

        '''
        return '<CF {0}: {1}>'.format(self.__class__.__name__, str(self))


    def __str__(self):
        '''x.__str__() <==> str(x)

        '''
        yyy = [x if y is None else '{0:0>2}'.format(y)
               for x, y in zip(('Y', 'M', 'D', 'h', 'm', 's'),
                               self.offset)]
     
        return '{0} ({1}-{2}-{3} {4}:{5}:{6})'.format(self.iso, *yyy)

   
    def __ge__(self, other):
        '''The rich comparison operator ``>=``

    x__ge__(y) <==> x>=y

        '''

        if isinstance(other, (self.__class__, int, float, Data)):
            return bool(self._binary_operation(other, '__ge__'))

        return NotImplemented


    def __gt__(self, other):
        '''The rich comparison operator ``>``

    x__gt__(y) <==> x>y

        '''

        if isinstance(other, (self.__class__, int, float, Data)):
            return bool(self._binary_operation(other, '__gt__'))

        return NotImplemented


    def __le__(self, other):
        '''The rich comparison operator ``<=``

    x__le__(y) <==> x<=y

        '''
        if isinstance(other, (self.__class__, int, float, Data)):
            return bool(self._binary_operation(other, '__le__'))
        
        return NotImplemented


    def __lt__(self, other):
        '''The rich comparison operator ``<``

    x__lt__(y) <==> x<y

        '''
        if isinstance(other, (self.__class__, int, float, Data)):
            return bool(self._binary_operation(other, '__lt__'))
        
        return NotImplemented


    def __eq__(self, other):
        '''The rich comparison operator ``==``

    x.__eq__(y) <==> x==y

        '''
        if isinstance(other, (self.__class__, int, float, Data)):
            return bool(self._binary_operation(other, '__eq__'))
        
        return NotImplemented


    def __ne__(self, other):
        '''The rich comparison operator ``!=``
        
    x__ne__(y) <==> x!=y

        '''
        if isinstance(other, (self.__class__, int, float, Data)):
            return bool(self._binary_operation(other, '__ne__'))

        return NotImplemented

    def __add__(self, other):
        '''The binary arithmetic operation ``+``

    x.__add__(y) <==> x + y

    .. versionadded:: 1.4

        '''     
        if isinstance(other, (self.__class__, int, float)):
            return self._binary_operation(other, '__add__')
        
        if hasattr(other, 'timetuple'):
            # other is a date-time object
            try:
                return self._datetime_arithmetic(other, __add__)
            except TypeError:
                return NotImplemented

        if isinstance(other, Data):
            return self._data_arithmetic(other, '__add__')
        
        return NotImplemented


    def __sub__(self, other):
        '''The binary arithmetic operation ``-``

    x.__sub__(y) <==> x - y

    .. versionadded:: 1.4

        '''
        if isinstance(other, (self.__class__, int, float)):
            return self._binary_operation(other, '__sub__')

        if isinstance(other, Data):
            return self._data_arithmetic(other, '__sub__')
        
        return NotImplemented


    def __mul__(self, other):
        '''The binary arithmetic operation ``*``

    x.__mul__(y) <==> x*y

        '''   
        if isinstance(other, (int, float)):
            return self._binary_operation(other, '__mul__')

        if isinstance(other, Data):
            return self._data_arithmetic(other, '__mul__')
        
        return NotImplemented


    def __div__(self, other):
        '''The binary arithmetic operation ``/``

    x.__div__(y) <==> x/y

        '''           
        if isinstance(other, (int, float)):
            return self._binary_operation(other, '__div__')

        if isinstance(other, Data):
            return self._data_arithmetic(other, '__div__')
        
        return NotImplemented


    def __floordiv__(self, other):
        '''The binary arithmetic operation ``//``

    x.__floordiv__(y) <==> x//y

        '''   
        if isinstance(other, (int, float)):
            return self._binary_operation(other, '__floordiv__')

        if isinstance(other, Data):
            return self._data_arithmetic(other, '__floordiv__')
        
        return NotImplemented

    
    def __truediv__(self, other):
        '''The binary arithmetic operation ``/`` (true division)

    x.__truediv__(y) <==> x/y

        '''   
        if isinstance(other, (int, float)):
            return self._binary_operation(other, '__truediv__')

        if isinstance(other, Data):
            return self._data_arithmetic(other, '__truediv__')
        
        return NotImplemented


    def __iadd__(self, other):
        '''The augmented arithmetic assignment ``+=``
    
    x.__iadd__(y) <==> x+=y
    
        '''
        if isinstance(other, (self.__class__, int, float)):
            return self._binary_operation(other, '__iadd__', True)

        return NotImplemented


    def __idiv__(self, other):
        '''The augmented arithmetic assignment ``/=``

    x.__idiv__(y) <==> x /= y

        '''
        if isinstance(other, (int, float)):
            return self._binary_operation(other, '__idiv__', True)

        return NotImplemented


    def __itruediv__(self, other):
        '''The augmented arithmetic assignment ``/=`` (true division)

    x.__truediv__(y) <==> x/y
        
        '''
        if isinstance(other, (int, float)):
            return self._binary_operation(other, '__itruediv__', True)

        return NotImplemented

    
    def __ifloordiv__(self, other):
        '''The augmented arithmetic assignment ``//=``

    x.__ifloordiv__(y) <==> x//=y

        '''
        if isinstance(other, (int, float)):
            return self._binary_operation(other, '__ifloordiv__', True)

        return NotImplemented


    def __imul__(self, other):
        '''The augmented arithmetic assignment ``*=``

    x.__imul__(y) <==> x *= y

        '''
        if isinstance(other, (int, float)):
            return self._binary_operation(other, '__imul__', True)

        return NotImplemented


    def __isub__(self, other):
        '''The augmented arithmetic assignment ``-=``

    x.__isub__(y) <==> x -= y

        '''
        if isinstance(other, (self.__class__, int, float)):
            return self._binary_operation(other, '__isub__', True)

        return NotImplemented


    def __imod__(self, other):
        '''The augmented arithmetic assignment ``%=``

    x.__imod__(y) <==> x%=y

        '''
        if isinstance(other, (int, float)):
            return self._binary_operation(other, '__imod__', True)

        return NotImplemented


    def __radd__(self, other):
        '''The binary arithmetic operation ``+`` with reflected operands

    x.__radd__(y) <==> y+x

        '''
        return self + other


    def __rmul__(self, other):
        '''The binary arithmetic operation ``*`` with reflected operands

    x.__rmul__(y) <==> y*x

        '''
        return self * other


    def __rsub__(self, other):
        '''The binary arithmetic operation ``-`` with reflected operands

    x.__rsub__(y) <==> y-x

    .. versionadded:: 1.4

        '''
        if isinstance(other, (self.__class__, int, float)):
            return self._binary_operation(other, '__rsub__')

        if hasattr(other, 'timetuple'):
            # other is a date-time object
            try:
                return self._datetime_arithmetic(other, __sub__)
            except:
                return NotImplemented

        return NotImplemented


    def __mod__(self, other):
        '''The binary arithmetic operation ``%``

    x.__mod__(y) <==> x % y
        
        '''   
        if isinstance(other, (self.__class__, int, float)):
            return self._binary_operation(other, '__mod__')

        return NotImplemented


    def __rmod__(self, other):
        '''The binary arithmetic operation ``%`` with reflected operands

    x.__rmod__(y) <==> y % x

        '''   
        if isinstance(other, (self.__class__, int, float)):
            return self._binary_operation(other, '__rmod__')

        return NotImplemented

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _binary_operation(self, other, method, inplace=False):
        '''TODO

        '''
        if inplace:
            new = self
        else:
            new = self.copy()

        self_units = self.duration.Units

        other = getattr(other, 'duration', other)

        duration = getattr(new.duration, method)(other)

        duration.squeeze(inplace=True)

        if duration.size != 1:           
            raise ValueError(
                "Can't create {} with more than one value: {!r}".format(
                    self.__class__.__name__, duration))
            
        if duration < 0:
            raise ValueError(
                "Can't create {} with with negative duration {!r}".format(
                    self.__class__.__name__, duration))

        if not duration.Units.equals(self.duration.Units):
            if method not in ('__eq__', '__ne__', '__lt__', '__le__', '__gt__', '__ge__'):
                # Operator is not one of ==, !=, >=, >, <=, <                
                raise ValueError(
                    "Can't create {} of {!r}".format(self.__class__.__name__, duration.Units))
        #--- End: if
        
        duration.Units = self_units

        new.duration = duration

        return new

    
    def _datetime_arithmetic(self, other, op):
        '''TODO

    .. versionadded:: 1.4

        '''
        def _dHMS(duration, other, calendar, op):
            units = Units('{0} since {1}'.format(duration.Units.units, other),
                          calendar)
            d = op(Data(0.0, units), duration)
            return d.dtarray.item(()) # TODO
        #--- End: def

        duration = self.duration
        units    = duration.Units

        if units == _calendar_years:
            months0 = duration.datum() * 12
            months = int(months0)
            if months != months0:
                raise ValueError(
                    "Fractional months not supported for date calculations: {}".format(
                        months0))
        elif units == _calendar_months:
            months0 = duration.datum()
            months = int(months0)
            if months != months0:
                raise ValueError(
                    "Fractional months not supported for date calculations: {}".format(
                        months0))
        else:
            months = None

        calendar = getattr(other, 'calendar', None)
        if calendar == '':
            calendar = None

        if months is not None:
            y, m = divmod(op(other.month, months), 12)            
            if not m:
                y -= 1
                m = 12
                
            y = other.year + y

            max_days = self.days_in_month(y, m, calendar)
            d = other.day
            if d > max_days:
                d = max_days

            return other.replace(year=y, month=m, day=d)
        else:
            return _dHMS(duration, other, calendar, op)
        

    def _data_arithmetic(self, other, method, inplace=False):
        '''TODO

        '''
        try:
            dt = other.datetime_array
        except ValueError:
            return self._binary_operation(other, method, inplace=inplace)
        else:
            out = []        
            for d in dt.flat:
                if d is numpy.ma.masked:
                    out.append(None)
                else:
                    out.append(getattr(self, method)(d))
            #--- End: for
            
            dt[...] = numpy.reshape(out, dt.shape)
    
            return Data(dt, units=other.Units)
        

    def _offset(self, dt):
        '''TODO

    .. versionadded:: 1.4

    :Parameters:
    
        dt: `cf.Datetime` TODO
    
    :Returns:
    
        `Datetime` TODO

        '''
        return cf_dt(*[(i if j is None else j)
                       for i, j in zip(elements(dt), self.offset)],
                     calendar=getattr(dt, 'calendar', None))


    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def iso(self):
        '''Return the time duration as an ISO 8601-like time duration string.

    .. versionadded:: 1.0
    
    **Examples:**
    
    >>> cf.TimeDuration(45, 'days').iso
    'P45D'
    >>> cf.TimeDuration(10, 'calendar_years').iso
    'P10Y'
    >>> cf.s(5.67).iso
    'PT5.67S'
    >>> cf.M(18.5).iso
    'P18.5M'

        '''
        duration = self.duration
        units    = duration.Units

        if units.equals(_calendar_months):
            return 'P{0}M'.format(duration.datum())
        if units.equals(_calendar_years):
            return 'P{0}Y'.format(duration.datum())
        if units.equals(_days):
            return 'P{0}D'.format(duration.datum())
        if units.equals(_hours):
            return 'PT{0}H'.format(duration.datum())
        if units.equals(_minutes):
            return 'PT{0}M'.format(duration.datum())
        if units.equals(_seconds):
            return 'PT{0}S'.format(duration.datum())

        raise ValueError(
            "Bad {0} units: {1!r}".format(self.__class__.__name__, units))

    
    @property
    def isint(self):
        '''True if the time duration is a whole number.

    .. versionadded:: 1.0
 
    **Examples:**
    
    >>> cf.TimeDuration(2, 'hours').isint
    True
    >>> cf.TimeDuration(2.0, 'hours').isint
    True
    >>> cf.TimeDuration(2.5, 'hours').isint
    False
    
        '''
        duration = self.duration

        if duration.dtype.kind == 'i':
            return True

        duration = duration.datum()
        return int(duration) == float(duration)

    
    @property
    def Units(self):
        '''The units of the time duration.

    .. versionadded:: 1.0
    
    **Examples:**
    
    >>> cf.TimeDuration(3, 'days').Units
    <CF Units: days>
    
    >>> t = cf.TimeDuration(cf.Data(12, 'calendar_months'))
    >>> t.Units
    <CF Units: calendar_months>
    >>> t.Units = cf.Units('calendar_years')
    >>> t.Units
    <CF Units: calendar_years>
    >>> t
    <CF TimeDuration: 1.0 calendar_years (from Y-01-01 00:00:00)>
    
        '''
        return self.duration.Units


    @Units.setter
    def Units(self, value):
        duration = getattr(self, 'duration', None)
        if duration is None:
            raise AttributeError("Can't set units when there is no duration attribute")

        self.duration.Units = Units(value)


    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self):
        '''Return a deep copy.

    ``t.copy()`` is equivalent to ``copy.deepcopy(t)``.
    
    .. versionadded:: 1.0
    
    :Returns:	
    
            The deep copy.
    
    **Examples:**
    
    >>> u = t.copy()

        '''
        new = TimeDuration.__new__(TimeDuration)
        new.__dict__ = self.__dict__.copy()
        new.duration = self.duration.copy()
        return new


    @classmethod
    def days_in_month(cls, year, month, calendar=None, leap_month=2,
                      month_lengths=None):
        '''The number of days in a specific month in a specific year in a
    specific calendar.

    .. versionadded:: 1.4
      
    :Parameters:
    
        year: `int`
    
        month: `int`
    
        calendar: `str`, optional
            By default, calendar is the mixed Gregorian/Julian
            calendar as defined by Udunits.
    
        leap_month: `int`, optional
            By default, the leap month is 2.
    
        month_lengths: sequence of `int`, optional
            By default, *month_lengths* is ``[31, 28, 31, 30, 31, 30,
            31, 31, 30, 31, 30, 31]``.
    
    :Returns:
    
        `int`
            The number of days in the specified month.
        
    **Examples:**
    
    >>> cf.TimeDuration.days_in_month(2004, 2, calendar='360_day')
    30

        '''
        if month_lengths is None:
            month_lengths = _default_month_lengths
        elif len(month_lengths) != 12:
            raise ValueError("month_lengths must be a sequence of 12 elements")

        month1 = month - 1
        
        if calendar in [None, 'standard', 'gregorian', 'proleptic_gregorian', '']:
            length = month_lengths[month1]
            if (month == leap_month and
                (year % 400 == 0 or (year % 100 != 0 and year % 4 == 0))):
                length += 1
        elif calendar == '360_day':
            length = 30
        elif calendar in ('noleap', '365_day'):
            length = month_lengths[month1]
        elif calendar in ('all_leap', '366_day'):
            length = month_lengths[month1]
            if month == leap_month:
                length += 1
        elif calendar == 'julian':
            length = month_lengths[month1]
            if month == leap_month and year % 4 == 0:
                length += 1

        return length


    def equals(self, other, rtol=None, atol=None, verbose=False,
               traceback=False):
        '''True if two time durations are equal.

    .. seealso:: `equivalent`
    
    .. versionadded:: 1.0
    
    :Parameters:
    
        other: 
            The object to compare for equality.
    
        atol: `float`, optional
            The absolute tolerance for all numerical comparisons, By
            default the value returned by the `ATOL` function is used.
    
        rtol: `float`, optional
            The relative tolerance for all numerical comparisons, By
            default the value returned by the `RTOL` function is used.
    
        traceback: `bool`, optional
            If True then print a traceback highlighting where the two
            instances differ.
    
    :Returns: 
    
        `bool`
            Whether or not the two instances are equal.
    
    **Examples:**
    
    >>> t = cf.TimeDuration(36, 'calendar_months')
    >>> u = cf.TimeDuration(3, 'calendar_years') 
    >>> t == u
    True
    >>> t.equals(u, traceback=True)
    TimeDuration: Different durations: <CF Data: 36 calendar_months>, <CF Data: 3 calendar_years>
    False

        '''
        if traceback:
            _DEPRECATION_ERROR_KWARGS(self, 'equals', traceback=True) # pragma: no cover
        
        # Check each instance's id
        if self is other:
            return True
 
        # Check that each instance is the same type
        if self.__class__ != other.__class__:
            if verbose: # pragma: no cover
                print("%s: Different type: %s" %
                      (self.__class__.__name__, other.__class__.__name__)) # pragma: no cover
            return False

        self__dict__  = self.__dict__.copy()
        other__dict__ = other.__dict__.copy()

        d0 = self__dict__.pop('duration', None)
        d1 = other__dict__.pop('duration', None)

        if not d0.equals(d1):
            if verbose: # pragma: no cover
                print("%s: Different durations: %r, %r" %
                      (self.__class__.__name__, d0, d1)) # pragma: no cover
            return False

        if self__dict__ != other__dict__:
            if verbose: # pragma: no cover
                print("%s: Different The default date-time elements: %r != %r" %
                      (self.__class__.__name__, self__dict__, other__dict__)) # pragma: no cover
            return False


        return True


    def equivalent(self, other, rtol=None, atol=None, verbose=True,
                   traceback=False):
        '''True if two time durations are logically equivalent.

    .. seealso:: `equals`
    
    .. versionadded:: 1.0
    
    :Parameters:
    
        other: 
            The object to compare for equivalence.
    
        atol: `float`, optional
            The absolute tolerance for all numerical comparisons, By
            default the value returned by the `ATOL` function is used.
    
        rtol: `float`, optional
            The relative tolerance for all numerical comparisons, By
            default the value returned by the `RTOL` function is used.
    
        traceback: `bool`, optional
            If True then print a traceback highlighting where the two
            instances differ.
    
    :Returns: 
    
        `bool`
            Whether or not the two instances logically equivalent.
    
    **Examples:**
    
    >>> t = cf.TimeDuration(36, 'calendar_months')
    >>> u = cf.TimeDuration(3, 'calendar_years') 
    >>> t == u
    True
    >>> t.equivalent(u)
    True
    >>> t.equals(u, traceback=True)
    TimeDuration: Different durations: <CF Data: 12 calendar_months>, <CF Data: 1 calendar_years>
    False

        '''
        if traceback:
            _DEPRECATION_ERROR_KWARGS(self, 'equivalent', traceback=True) # pragma: no cover        

        # Check each instance's id
        if self is other:
            return True
 
        # Check that each instance is the same type
        if self.__class__ != other.__class__:
            if verbose: # pragma: no cover
                print("%s: Different type: %s" %
                      (self.__class__.__name__, other.__class__.__name__)) # pragma: no cover
            return False

        self__dict__  = self.__dict__.copy()
        other__dict__ = other.__dict__.copy()

        d0 = self__dict__.pop('duration', None)
        d1 = other__dict__.pop('duration', None)
        if d0 != d0:
            if verbose: # pragma: no cover
                print("%s: Non-equivalent durations: %r, %r" %
                      (self.__class__.__name__, d0, d1)) # pragma: no cover
            return False

        if self__dict__ != other__dict__:
            if verbose: # pragma: no cover
                print("%s: Non-equivalent default date-time elements: %r != %r" %
                      (self.__class__.__name__, self__dict__, other__dict__)) # pragma: no cover
            return False

        return True


    def inspect(self):
        '''Inspect the attributes.

    .. seealso:: `cf.inspect`
    
    .. versionadded:: 1.0
    
    :Returns: 
    
        `None`

        '''
        print(cf_inspect(self)) # pragma: no cover


    def interval(self, dt, end=False, iso=None): # calendar=None,
        '''Return a time interval of exactly the time duration.

    The start (or end, if the *end* parameter is True) date-time of
    the time interval is determined by the *year*, *month*, *day*,
    *hour*, *minute* and *second* parameters, but if any of these is
    unset then its default value is taken from the attribute of the
    same name (i.e. the `!year`, `!month`, `!day`, `!hour`, `!minute`
    and `!second` attributes respectively).
    
    .. seealso:: `bounds`
    
    .. versionadded:: 1.0
    
    :Parameters:
    
        year, month, day, hour, minute, second: `int`, optional  TODO
            The date-time of the start (or end) of the time
            interval. If any parameter is unset then its value
            defaults to the attribute of the same name. The time
            interval calculation requires that all of the parameters
            have numerical values, so if an unset parameter has a
            corresponding attribute whose value is `None` then an
            exception will be raised.
            
            *Parameter example:*
              ``t.interval(year=1999, day=16)`` is equivalent to
              ``t.interval(1999, t.month, 16, t.hour, t.minute,
              t.second)``.
    
        end: `bool`, optional
            If True then the date-time given by the *year*, *month*,
            *day*, *hour*, *minute* and *second* parameters defines
            the end of the time interval. By default it defines the
            start of the time interval.
    
#        calendar: `str`, optional
#            Define the CF calendar for the input date-time and output
#            time interval. By default the calendar of the input
#            date-time is used. If *calendar* is set, then the calendar
#            of the input date-time is overridden.
#    
#            *Parameter example:*
#               To set a calendar without leap years:
#               ``calendar='noleap'``.
    
        iso: `str`, optional
            Return the time interval as an ISO 8601 time interval
            string rather than the default of a tuple of date-time
            objects. Valid values are (with example outputs for the
            time interval "3 years from 2007-03-01 13:00:00"):
    
              ========================  =============================================
              iso                       Example output
              ========================  =============================================
              ``'start and end'``       ``'2007-03-01 13:00:00/2010-03-01 13:00:00'``
              ``'start and duration'``  ``'2007-03-01 13:00:00/P3Y'``
              ``'duration and end'``    ``'P3Y/2010-03-01 13:00:00'``
              ========================  =============================================
    
    :Returns:
    
            The date-times at each end of the time interval. The first
            date-time is always earlier than or equal to the second
            date-time. If *iso* has been set then an ISO 8601 time
            interval string is returned instead of a tuple.
    
    **Examples:**
    
    >>> cf.TimeDuration(1, 'calendar_years').interval(1999)
    (<CF Datetime: 1999-01-01 00:00:00>, <CF Datetime: 2000-01-01 00:00:00>)
    
    >>> cf.TimeDuration(1, 'calendar_months').interval(1999, 12)
    (<CF Datetime: 1999-12-01 00:00:00>, <CF Datetime: 2000-01-01 00:00:00>)
    
    >>> cf.TimeDuration(2, 'calendar_years').interval(2000, 2, end=True)
    (<CF Datetime: 1998-02-01 00:00:00>, <CF Datetime: 2000-02-01 00:00:00>)
    
    >>> cf.TimeDuration(30, 'days').interval(1983, 12, 1, 6)
    (<CF Datetime: 1983-12-01 06:00:00>, <CF Datetime: 1983-12-31 06:00:00>)
    
    >>> cf.TimeDuration(30, 'days').interval(1983, 12, 1, 6, end=True)
    (<CF Datetime: 1983-11-01 06:00:00>, <CF Datetime: 1983-12-01 06:00:00>)
    
    >>> cf.TimeDuration(0, 'days').interval(1984, 2, 3)
    (<CF Datetime: 1984-02-03 00:00:00>, <CF Datetime: 1984-02-03 00:00:00>)
    
    >>> cf.TimeDuration(5, 'days', hour=6).interval(2004, 3, 2, end=True)
    (<CF Datetime: 2004-02-26 06:00:00>, <CF Datetime: 2004-03-02 06:00:00>)
    
    >>> cf.TimeDuration(5, 'days', hour=6).interval(2004, 3, 2, end=True, calendar='noleap')
    (<CF Datetime: 2004-02-25 06:00:00>, <CF Datetime: 2004-03-02 06:00:00>)
    
    >>> cf.TimeDuration(5, 'days', hour=6).interval(2004, 3, 2, end=True, calendar='360_day')
    (<CF Datetime: 2004-02-27 06:00:00>, <CF Datetime: 2004-03-02 06:00:00>)
    
    >>> cf.TimeDuration(5, 'days', hour=6).interval(2004, 3, 2, 13, end=True)
    (datetime.datetime(2004, 2, 26, 13, 0), <CF Datetime: 2004-03-02 13:00:00>)
    
    >>> cf.TimeDuration(19897.546, 'hours').interval(1984, 2, 3, 0)
    (<CF Datetime: 1984-02-03 00:00:00>, <CF Datetime: 1986-05-12 01:32:46>)
    
    >>> cf.TimeDuration(19897.546, 'hours').interval(1984, 2, 3, 0, end=True)
    (<CF Datetime: 1981-10-26 22:27:14>, <CF Datetime: 1984-02-03 00:00:00>)
    
    Create `cf.Query` objects for a time interval - one including both
    bounds and one which excludes the upper bound:
    
    >>> t = cf.TimeDuration(2, 'calendar_years')
    >>> interval = t.interval(1999, 12)
    >>> c = cf.wi(*interval)
    >>> c
    <CF Query: (wi [<CF Datetime: 1999-12-01 00:00:00>, <CF Datetime: 2001-01-01 00:00:00>])>
    >>> d = cf.ge(interval[0]) & cf.lt(interval[1])
    >>> d
    <CF Query: [(ge <CF Datetime: 1999-12-01 00:00:00>) & (lt <CF Datetime: 2000-01-01 00:00:00>)]>
    >>> c == cf.dt('2001-1-1')
    True
    >>> d == cf.dt('2001-1-1')
    False
    
    Create a `cf.Query` object which may be used to test where a time
    coordinate object's bounds lie inside a time interval:
    
    >>> t = cf.TimeDuration(1, 'calendar_months')
    >>> c = cf.cellwi(*t.interval(2000, 1, end=True))
    >>> c
    <CF Query: [lower_bounds(ge <CF Datetime: 1999-12-01 00:00:00>) & upper_bounds(le <CF Datetime: 2000-01-01 00:00:00>)]>
    
    Create ISO 8601 time interval strings:
    
    >>> t = cf.TimeDuration(6, 'calendar_years')
    >>> t.interval(1999, 12, end=True, iso='start and end') 
    '1993-12-01 00:00:00/1999-12-01 00:00:00'
    >>> t.interval(1999, 12, end=True, iso='start and duration')
    '1993-12-01 00:00:00/P6Y'
    >>> t.interval(1999, 12, end=True, iso='duration and end')
    'P6Y/1999-12-01 00:00:00'

        '''   
        def _dHMS(duration, dt, end):
            calendar = dt.calendar
            if not calendar:
                calendar = None
                
            units = Units('{0} since {1}'.format(duration.Units.units, dt),
                          calendar)
            dt1 = Data(0.0, units) 

            if not end:
                dt1 += duration
            else:
                dt1 -= duration

            dt1 = dt1.dtarray.item(()) # TODO

            if not end:
                return dt, dt1 #dt.copy(), dt1
            else:
                return dt1, dt # dt1, dt.copy()
        #--- End: def

        calendar = getattr(dt, 'calendar', _default_calendar)
        if calendar == '':
            calendar = _default_calendar
            
        dt = cf_dt(dt, calendar=calendar)
        
        duration = self.duration
        units    = duration.Units

        if units == _calendar_years:
            months = duration.datum() * 12
            int_months = int(months)
            if int_months != months:
                raise ValueError(
                    "Can't create a time interval of a non-integer number of calendar months: {0}".format(
                        months))
        elif units == _calendar_months:
            months = duration.datum()
            int_months = int(months)
            if int_months != months:
                raise ValueError(
                    "Can't create a time interval of a non-integer number of calendar months: {0}".format(
                        months))
        else:
            int_months = None

        if int_months is not None:
            if not end:
                y, month1 = divmod(dt.month + int_months, 12)
                
                if not month1:
                    y -= 1
                    month1 = 12
                
                year1  = dt.year + y
                
                max_days = self.days_in_month(year1, month1, calendar)
                
                day1 = dt.day
                if day1 > max_days:
                    day1 = max_days

                dt0 = dt #.copy()
                dt1 = dt.replace(year=year1, month=month1, day=day1)
            else:
                y, month0 = divmod(dt.month - int_months, 12)
                
                if not month0:
                    y -= 1
                    month0 = 12
                
                year0  = dt.year + y

                max_days = self.days_in_month(year0, month0, calendar)
                day0 = dt.day
                if day0 > max_days:
                    day0 = max_days          

                dt0 = dt.replace(year=year0, month=month0, day=day0)
                dt1 = dt #0.copy()
        else:
            dt0, dt1 = _dHMS(duration, dt, end)

        if not iso:
            return dt0, dt1
             
        if iso == 'start and end':
            return '{0}/{1}'.format(dt0, dt1)
        if iso == 'start and duration':
            return '{0}/{1}'.format(dt0, self.iso)
        if iso == 'duration and end':
            return '{0}/{1}'.format(self.iso, dt1)


    def bounds(self, dt, direction=True): #calendar=None, 
        '''Return a time interval containing a date-time.

    The interval spans the time duration and starts and ends at
    date-times consistent with the time duration's offset.
    
    .. seealso:: `cf.dt`, `cf.Datetime`, `interval` TODO
    
    .. versionadded:: 1.2.3
    
    :Parameters:
    
        dt: date-time-like
            The date-time to be contained by the interval. *dt* may be
            any date-time-like object, such as `cf.Datetime`,
            `datetime.datetime`, `netCDF4.netcdftime.datetime`, etc.
    
            *Parameter example:*
              To find bounds around 1999-16-1 in the Gregorian
              calendar you could use ``dt=cf.dt(1999, 1, 16)`` or
              ``dt=datetime.datetime(1999, 1, 16)`` (See `cf.dt` for
              details).
    
        calendar: `str`, optional
            Define the CF calendar for the input date-time and output
            time interval. By default the calendar of the input
            date-time is used. If *calendar* is set, then the calendar
            of the input date-time is overridden.
    
            *Parameter example:*
              To set a calendar without leap years:
              ``calendar='noleap'``.
     
        direction: `bool`, optional
            If `False` then the bounds are decreasing. By default the
            bounds are increasing. Note that ``t.bounds(dt,
            direction=False)`` is equivalent to
            ``t.bounds(dt)[::-1]``.
            
    :Returns:
    
        (`cf.Datetime`, `cf.Datetime`) TODO
            
    **Examples:**
    
    TODO
    
    >>> t = cf.M()
    >>> t.bounds(cf.dt(2000, 1, 1))
    (<CF Datetime: 2000-1-1 00:00:00>, <CF Datetime: 2000-2-1 00:00:00>) TODO
    >>> t.bounds(cf.dt(2000, 1, 1))
    (<CF Datetime: 2000-1-1 00:00:00>, <CF Datetime: 2000-2-1 00:00:00>)
    
    >>> t = cf.M(1)
    >>> t.bounds(cf.dt(2000, 3, 1))
    (<CF Datetime: 2000-03-01 00:00:00>, <CF Datetime: 2000-04-01 00:00:00>)
    
    >>> t = cf.M(1, day=15)
    >>> t.bounds(cf.dt(2000, 3, 1))
    (<CF Datetime: 2000-02-15 00:00:00>, <CF Datetime: 2000-03-15 00:00:00>)
    
    >>> t = cf.M(2, day=15)
    >>> t.bounds(cf.dt(2000, 3, 1), direction=False)
    (<CF Datetime: 2000-03-15 00:00:00>, <CF Datetime: 2000-01-15 00:00:00>)

        '''
        abs_self = abs(self)
 
        calendar = getattr(dt, 'calendar', _default_calendar)
        if calendar == '':
            calendar = _default_calendar
            
        dt = cf_dt(dt, calendar=calendar)

        dt0 = self._offset(dt)

        if dt0 > dt:
            dt1 = dt0
            dt0 = dt1 - abs_self
        else:
            dt1 = dt0 + abs_self

        if direction:
            return (dt0, dt1)
        else:
            return (dt1, dt0)


    def is_day_factor(self):
        '''Return True if an integer multiple of the time duration is equal to
    one day.

    .. versionadded:: 1.0
    
    :Returns:	
    
        `bool`
    
    **Examples:**
    
    >>> cf.TimeDuration(0.5, 'days').is_day_factor()
    True
    
    >>> cf.TimeDuration(1, 'days').is_day_factor()
    True
    >>> cf.TimeDuration(0.25, 'days').is_day_factor()
    True
    >>> cf.TimeDuration(0.3, 'days').is_day_factor()
    False
    >>> cf.TimeDuration(2, 'days').is_day_factor()
    False
    
    >>> cf.TimeDuration(24, 'hours').is_day_factor()
    True
    >>> cf.TimeDuration(6, 'hours').is_day_factor()
    True
    >>> cf.TimeDuration(7, 'hours').is_day_factor()
    False
    >>> cf.TimeDuration(27, 'hours').is_day_factor()
    False
    
    >>> cf.TimeDuration(1440, 'minutes').is_day_factor()
    True
    >>> cf.TimeDuration(15, 'minutes').is_day_factor()
    True
    >>> cf.TimeDuration(17, 'minutes').is_day_factor()
    False
    >>> cf.TimeDuration(2007, 'minutes').is_day_factor()
    False
    
    >>> cf.TimeDuration(86400, 'seconds').is_day_factor()
    True
    >>> cf.TimeDuration(45, 'seconds').is_day_factor()
    True
    >>> cf.TimeDuration(47, 'seconds').is_day_factor()
    False
    >>> cf.TimeDuration(86401, 'seconds').is_day_factor()
    False
    
    >>> cf.TimeDuration(1, 'calendar_months').is_day_factor()
    False
    >>> cf.TimeDuration(1, 'calendar_years').is_day_factor()
    False

        '''
        try:
            return not Data(1, 'day') % self.duration
        except ValueError:
            return False


#--- End: class


def Y(duration=1, month=1, day=1, hour=0, minute=0, second=0):
    '''Return a time duration of calendar years in a `cf.TimeDuration`
    object.

    ``cf.Y()`` is equivalent to ``cf.TimeDuration(1,
    'calendar_year')``.
    
    ``cf.Y(duration, *args, **kwargs)`` is equivalent to
    ``cf.TimeDuration(duration, 'calendar_year', *args, **kwargs)``.
    
    .. seealso:: `cf.M`, `cf.D`, `cf.h`, `cf.m`, `cf.s`
    
    .. versionadded:: 1.0
    
    :Parameters:
    
        duration: number, optional
            The number of calendar years in the time duration.
    
        month, day, hour, minute, second: `int`, optional
            The default date-time elements for defining the start and
            end of a time interval based on this time duration. See
            `cf.TimeDuration` and `cf.TimeDuration.interval` for
            details.
    
            *Parameter example:*
              ``cf.Y(month=12)`` is equivalent to ``cf.TimeDuration(1,
              'calendar_years', month=12)``.
    
    :Returns:
    
        `cf.TimeDuration`
            The new `cf.TimeDuration` object.
    
    **Examples:**
    
    >>> cf.Y()
    <CF TimeDuration: 1 calendar year (from Y-01-01 00:00:00)>
    
    >>> cf.Y(10, month=12)   
    <CF TimeDuration: 10 calendar years (from Y-12-01 00:00:00)>
    
    >>> cf.Y(15, month=4, day=2, hour=12, minute=30, second=2)  
    <CF TimeDuration: 15 calendar years (from Y-04-02 12:30:02)>
    
    >>> cf.Y(0)       
    <CF TimeDuration: 0 calendar years (from Y-01-01 00:00:00)>

    '''
    return TimeDuration(duration, 'calendar_years', month=month,
                        day=day, hour=hour, minute=minute,
                        second=second)


def M(duration=1, month=1, day=1, hour=0, minute=0, second=0):
    '''Return a time duration of calendar months in a `cf.TimeDuration`
object.
    
    ``cf.M()`` is equivalent to ``cf.TimeDuration(1, 'calendar_month')``.
    
    .. seealso:: `cf.Y`, `cf.D`, `cf.h`, `cf.m`, `cf.s`
    
    .. versionadded:: 1.0
    
    :Parameters:
    
        duration: number, optional
            The number of calendar months in the time duration.
    
        year, month, day, hour, minute, second: `int`, optional
            The default date-time elements for defining the start and
            end of a time interval based on this time duration. See
            `cf.TimeDuration` and `cf.TimeDuration.interval` for
            details.
    
            *Parameter example:*
              ``cf.M(day=16)`` is equivalent to ``cf.TimeDuration(1,
              'calendar_months', day=16)``.
    
    :Returns:
    
        `TimeDuration`
            The new `cf.TimeDuration` object.
    
    **Examples:**
    
    >>> cf.M()
    <CF TimeDuration: 1 calendar month (from Y-M-01 00:00:00)>
    
    >>> cf.M(3, day=16)
    <CF TimeDuration: 3 calendar months (from Y-M-16 00:00:00)>
    
    >>> cf.M(24, day=2, hour=12, minute=30, second=2)
    <CF TimeDuration: 24 calendar months (from Y-M-02 12:30:02)>
    
    >>> cf.M(0)
    <CF TimeDuration: 0 calendar months (from Y-M-01 00:00:00)>

    '''
    return TimeDuration(duration, 'calendar_months', month=month, day=day, 
                        hour=hour, minute=minute, second=second)


def D(duration=1, month=1, day=1, hour=0, minute=0, second=0):
    '''Return a time duration of days in a `cf.TimeDuration` object.

    ``cf.D()`` is equivalent to ``cf.TimeDuration(1, 'day')``.
    
    .. seealso:: `cf.Y`, `cf.M`, `cf.h`, `cf.m`, `cf.s`
    
    .. versionadded:: 1.0
    
    :Parameters:
    
        duration: number, optional
            The number of days in the time duration.
    
        month, day, hour, minute, second: `int`, optional
            The default date-time elements for defining the start and end
            of a time interval based on this time duration. See
            `cf.TimeDuration` and `cf.TimeDuration.interval` for details.
    
            *Parameter example:*
               ``cf.D(hour=12)`` is equivalent to ``cf.TimeDuration(1,
               'day', hour=12)``.
    
    :Returns:
    
        `cf.TimeDuration`
            The new `cf.TimeDuration` object.
    
    **Examples:**
    
    >>> cf.D()
    <CF TimeDuration: 1 day (from Y-M-D 00:00:00)>
    
    >>> cf.D(5, hour=12)       
    <CF TimeDuration: 5 days (from Y-M-D 12:00:00)>
    
    >>> cf.D(48.5, minute=30)
    <CF TimeDuration: 48.5 days (from Y-M-D 00:30:00)>
    
    >>> cf.D(0.25, hour=6, minute=30, second=20)
    <CF TimeDuration: 0.25 days (from Y-M-D 06:30:20)>
    
    >>> cf.D(0)
    <CF TimeDuration: 0 days (from Y-M-D 00:00:00)>

    '''
    return TimeDuration(duration, 'days', month=month, day=day, 
                        hour=hour, minute=minute, second=second)


def h(duration=1, month=1, day=1, hour=0, minute=0, second=0):
    '''Return a time duration of hours in a `cf.TimeDuration` object.

``cf.h()`` is equivalent to ``cf.TimeDuration(1, 'hour')``.

.. seealso:: `cf.Y`, `cf.M`, `cf.D`, `cf.m`, `cf.s`

.. versionadded:: 1.0

:Parameters:

    duration: number, optional
        The number of hours in the time duration.

    year, month, day, hour, minute, second: `int`, optional
        The default date-time elements for defining the start and end
        of a time interval based on this time duration. See
        `cf.TimeDuration` and `cf.TimeDuration.interval` for details.

        *Parameter example:*
          ``cf.h(minute=30)`` is equivalent to ``cf.TimeDuration(1,
          'hour', minute=30)``.

:Returns:

    `cf.TimeDuration`
        The new `cf.TimeDuration` object.

**Examples:**

>>> cf.h()
<CF TimeDuration: 1 hour (from Y-M-D h:00:00)>

>>> cf.h(3, minute=15)
<CF TimeDuration: 3 hours (from Y-M-D h:15:00)>

>>> cf.h(0.5)
<CF TimeDuration: 0.5 hours (from Y-M-D h:00:00)>

>>> cf.h(6.5, minute=15, second=45)
<CF TimeDuration: 6.5 hours (from Y-M-D h:15:45)>

>>> cf.h(0)
<CF TimeDuration: 0 hours (from Y-M-D h:00:00)>

    '''
    return TimeDuration(duration, 'hours', month=month, day=day,
                        hour=hour, minute=minute, second=second)
#--- End: def

def m(duration=1, month=1, day=1, hour=0, minute=0, second=0):
    '''Return a time duration of minutes in a `cf.TimeDuration` object.

``cf.m()`` is equivalent to ``cf.TimeDuration(1, 'minute')``.

.. seealso:: `cf.Y`, `cf.M`, `cf.D`, `cf.h`, `cf.s`

.. versionadded:: 1.0

:Parameters:

    duration: number, optional
        The number of hours in the time duration.

    month, day, hour, minute, second: `int`, optional
        The default date-time elements for defining when a time
        interval based on this time duration begins or ends. See
        `cf.TimeDuration` and `cf.TimeDuration.interval` for details.

        *Parameter example:*
          ``cf.m(second=30)`` is equivalent to ``cf.TimeDuration(1,
          'minute', second=30)``.

:Returns:

    `cf.TimeDuration`
        The new `cf.TimeDuration` object.

**Examples:**

>>> cf.m()
<CF TimeDuration: 1 minute (from Y-M-D h:mm:00)>

>>> cf.m(30, second=15)
<CF TimeDuration: 30 minutes (from Y-M-D h:mm:15)>

>>> cf.m(0.5)
<CF TimeDuration: 0.5 minutes (from Y-M-D h:mm:00)>

>>> cf.m(2.5, second=45)
<CF TimeDuration: 2.5 minutes (from Y-M-D h:mm:45)>

>>> cf.m(0)
<CF TimeDuration: 0 minutes (from Y-M-D h:mm:00)>

    '''
    return TimeDuration(duration, 'minutes', month=month, day=day, 
                        hour=hour, minute=minute, second=second)
#--- End: def

def s(duration=1, month=1, day=1, hour=0, minute=0, second=0):
    '''Return a time duration of seconds in a `cf.TimeDuration` object.

``cf.s()`` is equivalent to ``cf.TimeDuration(1, 'second')``.

.. seealso:: `cf.Y`, `cf.M`, `cf.D`, `cf.h`, `cf.m`

.. versionadded:: 1.0

:Parameters:

    duration: number, optional
        The number of hours in the time duration.

    month, day, hour, minute, second: `int`, optional
        The default date-time elements for defining the start and end
        of a time interval based on this time duration. See
        `cf.TimeDuration` and `cf.TimeDuration.interval` for details.

        *Parameter example:*
          ``cf.s(hour=6)`` is equivalent to ``cf.TimeDuration(1,
          'seconds', hour=6)``.

:Returns:

    `cf.TimeDuration`
        The new `cf.TimeDuration` object.

**Examples:**

>>> cf.s()   
<CF TimeDuration: 1 second (from Y-M-D h:m:s)>

>>> cf.s().interval(1999, 12, 1)
(<CF Datetime: 1999-12-01 00:00:00>, datetime.datetime(1999, 12, 1, 0, 0, 1))

>>> cf.s(30)
<CF TimeDuration: 30 seconds (from Y-M-D h:m:s)>

>>> cf.s(0.5)
<CF TimeDuration: 0.5 seconds (from  Y-M-D h:m:s)>

>>> cf.s(12.25)
<CF TimeDuration: 12.25 seconds (from Y-M-D h:m:s)>

>>> cf.s(2.5, year=1999, hour=12)
<CF TimeDuration: 2.5 seconds (from 1999-01-01 12:00:00)>

>>> cf.s(0)
<CF TimeDuration: 0 seconds (from Y-01-01 00:00:00)>

    '''
    return TimeDuration(duration, 'seconds', month=month, day=day, 
                        hour=hour, minute=minute, second=second)
#--- End: def
