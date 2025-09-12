const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const app = express();

// Enable CORS for all routes
app.use(cors());

// Init Middleware to accept JSON body data
app.use(express.json({ extended: false }));

// --- Connect to Database ---
const db = process.env.MONGO_URI; // Get this from your MongoDB Atlas dashboard

mongoose.connect(db, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
}).then(() => console.log('MongoDB Connected...'))
  .catch(err => console.log(err));

// --- Define Routes ---
app.get('/', (req, res) => res.send('API Running'));

// Use the routes we will create
app.use('/api/users', require('./routes/users')); // For registration
app.use('/api/auth', require('./routes/auth'));   // For login
app.use('/api/products', require('./routes/products'));


const PORT = process.env.PORT || 5000;

app.listen(PORT, () => console.log(`Server started on port ${PORT}`));