const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const auth = require('../middleware/auth'); // We'll use auth middleware later
require('dotenv').config();

// @route   POST api/users
// @desc    Register a user
// @access  Public (for initial admin) / Private (admin only for subsequent users)
router.post('/', async (req, res) => {
    const { email, password, role } = req.body;

    try {
        // Check if any users exist. If not, the first registered user is admin.
        const existingUsers = await User.find();
        const isFirstUser = existingUsers.length === 0;

        if (!isFirstUser) {
            // If not the first user, require admin authentication
            auth(req, res, async () => {
                if (req.user.role !== 'admin') {
                    return res.status(403).json({ msg: 'Authorization denied: Only admins can register new users' });
                }
            });
        }

        // Check if the provided role is allowed (if not the first user)
        if (!isFirstUser && role !== 'vendor' && role !== 'admin') {
            return res.status(400).json({ msg: 'Invalid role specified' });
        }

        let user = await User.findOne({ email });
        if (user) {
            return res.status(400).json({ msg: 'User already exists' });
        }

        user = new User({
            email,
            password,
            role: isFirstUser ? 'admin' : role // Set role, default to 'admin' if first user
        });

        const salt = await bcrypt.genSalt(10);
        user.password = await bcrypt.hash(password, salt);

        await user.save();

        const payload = {
            user: {
                id: user.id,
                role: user.role // Include role in the token
            }
        };

        jwt.sign(payload, process.env.JWT_SECRET, { expiresIn: '1h' }, (err, token) => {
            if (err) throw err;
            res.json({ token });
        });
    } catch (err) {
        console.error(err.message);
        res.status(500).send('Server Error');
    }
});

module.exports = router;