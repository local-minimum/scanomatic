import PropTypes from 'prop-types';

export const jobType = PropTypes.shape({
    duration: PropTypes.shape({
        days: PropTypes.number.isRequired,
        hours: PropTypes.number.isRequired,
        minutes: PropTypes.number.isRequired,
    }).isRequired,
    name: PropTypes.string.isRequired,
    interval: PropTypes.number.isRequired,
});
