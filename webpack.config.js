module.exports = {
    entry: {
        ccc: ['./scanomatic/ui_server_data/js/src/ccc_index.jsx'],
        scanning: ['./scanomatic/ui_server_data/js/src/scanning_index.jsx'],
    },
    output: {
        filename: 'scanomatic/ui_server_data/js/[name].js',
    },
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                },
            },
            {
                test: /\.png$/,
                use: {
                    loader: 'file-loader',
                },
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader'],
            },
        ],
    },
    resolve: {
        extensions: ['.js', '.json', '.jsx'],
    },
};
