<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="utf-8">
<meta name="viewport"
	content="width=device-width, initial-scale=1, shrink-to-fit=no">
<meta name="description" content="">
<meta name="author" content="">

<title>Data Visualization - Assign2-Hardik Shah</title>

<!-- Font Awesome Icons -->
<link href="vendor/fontawesome-free/css/all.min.css" rel="stylesheet"
	type="text/css">

<!-- Google Fonts -->
<link
	href="https://fonts.googleapis.com/css?family=Merriweather+Sans:400,700"
	rel="stylesheet">
<link
	href='https://fonts.googleapis.com/css?family=Merriweather:400,300,300italic,400italic,700,700italic'
	rel='stylesheet' type='text/css'>

<!-- Plugin CSS -->
<link href="vendor/magnific-popup/magnific-popup.css" rel="stylesheet">

<!-- Theme CSS - Includes Bootstrap -->
<link href="css/creative.min.css" rel="stylesheet">
<link rel="stylesheet"
	href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-notify/0.2.0/css/bootstrap-notify.css" />

<link rel="stylesheet" href="leaflet.css" />


<style>
.legend {
	font-family: 'Raleway', sans-serif;
	fill: #333333;
}

.tooltip {
	fill: #333333;
}

select {
	-webkit-appearance: none;
	-moz-appearance: none;
	-ms-appearance: none;
	appearance: none;
	outline: 0;
	box-shadow: none;
	border: 0 !important;
	background: #2c3e50;
	background-image: none;
	/*font-size: 12px;*/
}
/* Custom Select */
.select {
	position: relative;
	display: block;
	width: 20em;
	height: 3em;
	line-height: 3;
	background: #2c3e50;
	overflow: hidden;
	border-radius: .25em;
	font-size: 12px;
}

select {
	padding: 3px;
	color: #fff;
	cursor: pointer;
	border-radius: 10px;
}

select::-ms-expand {
	display: none;
}
/* Arrow */
.select::after {
	content: '\25BC';
	position: absolute;
	top: 0;
	right: 0;
	bottom: 0;
	padding: 0 1em;
	background: #34495e;
	pointer-events: none;
}
/* Transition */
.select:hover::after {
	color: #f39c12;
}

.select::after {
	-webkit-transition: .25s all ease;
	-o-transition: .25s all ease;
	transition: .25s all ease;
}

.Visualize {
	margin-left: 35px;
	margin-right: 35px;
}

.submitButton {
	font-size: 20px !important;
	background-color: #f4623a;
	font-weight: bold;
	text-shadow: 1px 1px #F36C8C;
	color: #ffffff;
	border-radius: 100px;
	-moz-border-radius: 100px;
	-webkit-border-radius: 100px;
	border: 1px solid #F36C8C;
	cursor: pointer;
	box-shadow: 0 1px 0 rgba(255, 255, 255, 0.5) inset;
	-moz-box-shadow: 0 1px 0 rgba(255, 255, 255, 0.5) inset;
	-webkit-box-shadow: 0 1px 0 rgba(255, 255, 255, 0.5) inset;
}

.axis path, .axis line {
	fill: none;
	stroke: #000;
	shape-rendering: crispEdges;
}

.dot {
	stroke: #000;
}

.grad {
	background: #fc4a1a; /* fallback for old browsers */
	background: -webkit-linear-gradient(to right, #f7b733, #fc4a1a);
	/* Chrome 10-25, Safari 5.1-6 */
	background: linear-gradient(to right, #f7b733, #fc4a1a);
	/* W3C, IE 10+/ Edge, Firefox 16+, Chrome 26+, Opera 12+, Safari 7+ */
}

p, li {
	color: white !important;
}

#map {
	/*	width: 800px; */
	height: 500px;
}

.info {
	padding: 6px 8px;
	font: 14px/16px Arial, Helvetica, sans-serif;
	background: white;
	background: rgba(255, 255, 255, 0.8);
	box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
	border-radius: 5px;
}

.info h4 {
	margin: 0 0 5px;
	color: #777;
}

.legend {
	text-align: left;
	line-height: 18px;
	color: #555;
}

.legend i {
	width: 18px;
	height: 18px;
	float: left;
	margin-right: 8px;
	opacity: 0.7;
}
</style>
</head>

<body id="page-top">

	<!-- Navigation -->
	<nav class="navbar navbar-expand-lg navbar-light fixed-top py-3"
		id="mainNav">
		<div class="container">
			<a class="navbar-brand js-scroll-trigger" href="#page-top">Page-Top</a>
			<button class="navbar-toggler navbar-toggler-right" type="button"
				data-toggle="collapse" data-target="#navbarResponsive"
				aria-controls="navbarResponsive" aria-expanded="false"
				aria-label="Toggle navigation">
				<span class="navbar-toggler-icon"></span>
			</button>
			<div class="collapse navbar-collapse" id="navbarResponsive">
				<ul class="navbar-nav ml-auto my-2 my-lg-0">
					<li class="nav-item"><a class="nav-link js-scroll-trigger"
						href="#contact">Feedback</a></li>
				</ul>
			</div>
		</div>
	</nav>

	<!-- Masthead -->
	<header class="masthead">
		<div class="container h-100">
			<div
				class="row h-100 align-items-center justify-content-center text-center">
				<div class="col-lg-10 align-self-end">
					<h1 class="text-uppercase text-white font-weight-bold">Cloud Computing Project 1</h1>
					<hr class="divider my-4">
				</div>
				<div class="col-lg-8 align-self-baseline">
					<a class="btn btn-primary btn-xl js-scroll-trigger" href="#about">TEST</a>
				</div>
			</div>
		</div>
	</header>


	<!-- Contact Section -->
	<section class="page-section grad" id="contact"
		style="color: white !important">
		<div class="container">
			<div class="row justify-content-center">
				<div class="col-lg-8 text-center">
					<h2 class="mt-0">Provide you feedback</h2>
					<hr class="divider my-4">
					<p class="mb-5">Liked project? Send feedback!!! Didn't liked
						project? Send feedback!!!</p>
				</div>
			</div>
<!-- 		<div class="row">
				<div class="col-lg-4 ml-auto text-center">
					<i class="fas fa-phone fa-3x mb-3 text-muted"></i>
					<div>+1 (480) 434-1097</div>
				</div>
				<div class="col-lg-4 mr-auto text-center">
					<i class="fas fa-envelope fa-3x mb-3 text-muted"></i>
					<a class="d-block" style="color: white !important"
						href="mailto:contact@yourwebsite.com">hrshah5@asu.edu</a>
				</div>
			</div>  -->	
		</div>
	</section>

	<!-- Footer -->
	<footer class="bg-light py-5 grad">
		<div class="container">
			<div class="small text-center" style="color: white !important">Cloud Computing - Project 1 - AWS Web App</div>
		</div>
	</footer>

	<!-- Bootstrap core JavaScript -->
	<script src="vendor/jquery/jquery.min.js"></script>
	<script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>

	<!-- Plugin JavaScript -->
	<script src="vendor/jquery-easing/jquery.easing.min.js"></script>
	<script src="vendor/magnific-popup/jquery.magnific-popup.min.js"></script>

	<!-- Custom scripts for this template -->
	<script src="js/creative.min.js"></script>

	<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.6/d3.min.js"
		charset="utf-8"></script>
	<script
		src="https://cdnjs.cloudflare.com/ajax/libs/d3-legend/1.3.0/d3-legend.js"
		charset="utf-8"></script>
	<script src="js/radarChart.js"></script>
	<script
		src="https://cdnjs.cloudflare.com/ajax/libs/notify/0.4.2/notify.min.js"></script>

</body>

</html>
