// routes/products.js
const express = require('express');
const router = express.Router();
const Product = require('../models/product');

// --- Admin Dashboard (Read All) ---
// GET /admin
router.get('/', async (req, res) => {
    try {
        const products = await Product.find({});
        res.render('admin', { products: products });
    } catch {
        res.redirect('/');
    }
});

// --- Show Add Product Form (Create Part 1) ---
// GET /admin/add
router.get('/add', (req, res) => {
    res.render('add-product');
});

// --- Process Add Product Form (Create Part 2) ---
// POST /admin/add
router.post('/add', async (req, res) => {
    const product = new Product({
        name: req.body.name,
        category: req.body.category,
        description: req.body.description,
        details: req.body.details,
        price: req.body.price,
        priceUnit: req.body.priceUnit,
        imageUrl: req.body.imageUrl
    });
    try {
        await product.save();
        res.redirect('/admin');
    } catch (err) {
        console.error(err);
        res.render('add-product', { product: product, errorMessage: 'Error creating product' });
    }
});

// --- Show Edit Product Form (Update Part 1) ---
// GET /admin/edit/:id
router.get('/edit/:id', async (req, res) => {
    try {
        const product = await Product.findById(req.params.id);
        res.render('edit-product', { product: product });
    } catch {
        res.redirect('/admin');
    }
});

// --- Process Edit Product Form (Update Part 2) ---
// PUT /admin/edit/:id
router.put('/edit/:id', async (req, res) => {
    let product;
    try {
        product = await Product.findById(req.params.id);
        product.name = req.body.name;
        product.category = req.body.category;
        product.description = req.body.description;
        product.details = req.body.details;
        product.price = req.body.price;
        product.priceUnit = req.body.priceUnit;
        product.imageUrl = req.body.imageUrl;
        await product.save();
        res.redirect('/admin');
    } catch {
        if (product == null) {
            res.redirect('/admin');
        } else {
            res.render('edit-product', { product: product, errorMessage: 'Error updating product' });
        }
    }
});

// --- Delete Product ---
// DELETE /admin/delete/:id
router.delete('/delete/:id', async (req, res) => {
    try {
        await Product.findByIdAndDelete(req.params.id);
        res.redirect('/admin');
    } catch (err) {
        console.log(err);
        res.redirect('/admin');
    }
});


module.exports = router;