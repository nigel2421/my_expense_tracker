// models/product.js
const mongoose = require('mongoose');

const productSchema = new mongoose.Schema({
    name: {
        type: String,
        required: true,
        trim: true
    },
    category: {
        type: String,
        required: true,
        enum: ['Fencing', 'Quartz', 'Marble', 'Service'] // You can expand this list
    },
    description: {
        type: String,
        required: true
    },
    // Using a flexible 'details' field for things like mesh size, dimensions, etc.
    details: {
        type: String 
    },
    // Storing price as a number
    price: {
        type: Number,
        required: true,
        min: 0
    },
    priceUnit: {
        type: String, // e.g., "per panel", "per m²", "per MTR"
        required: true
    },
    imageUrl: {
        type: String // A URL to the product image
    }
});

module.exports = mongoose.model('Product', productSchema);