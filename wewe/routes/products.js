const express = require('express');
const router = express.Router();
const Product = require('../models/Product');

// GET all products
router.get('/', async (req, res) => {
    const products = await Product.find();
    res.send(products);
});

// POST a new product (for the admin)
router.post('/', async (req, res) => {
    let product = new Product({
        name: req.body.name,
        category: req.body.category,
        description: req.body.description,
        // ... and so on
    });
    product = await product.save();
    res.send(product);
});

// DELETE a product (for the admin)
router.delete('/:id', async (req, res) => {
    const product = await Product.findByIdAndRemove(req.params.id);
    if (!product) return res.status(404).send('The product with the given ID was not found.');
    res.send(product);
});

module.exports = router;