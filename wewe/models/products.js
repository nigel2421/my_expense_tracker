const mongoose = require('mongoose');

const productSchema = new mongoose.Schema({
    name: { type: String, required: true },
    category: { type: String, required: true },
    description: String,
    details: [ // Array for specifications like size, mesh, etc.
        {
            title: String,
            value: String
        }
    ],
    pricing: [ // Array for different pricing options
        {
            type: String, // e.g., "Galvanized", "per m²"
            price: Number
        }
    ],
    imageUrl: String
});

const Product = mongoose.model('Product', productSchema);

module.exports = Product;