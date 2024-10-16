-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Oct 11, 2024 at 10:15 AM
-- Server version: 5.7.33
-- PHP Version: 8.1.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `traffic`
--

-- --------------------------------------------------------

--
-- Table structure for table `detection_result`
--

CREATE TABLE `detection_result` (
  `id` int(11) NOT NULL,
  `upload_datetime` datetime NOT NULL,
  `location` varchar(50) NOT NULL,
  `mean_motorcycle` float NOT NULL,
  `mean_car` float NOT NULL,
  `mean_total_objects_in_box` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `detection_result`
--

INSERT INTO `detection_result` (`id`, `upload_datetime`, `location`, `mean_motorcycle`, `mean_car`, `mean_total_objects_in_box`) VALUES
(1, '2024-10-11 16:52:00', 'Pasar Banyumanik', 2.87, 2.19, 5.06);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `detection_result`
--
ALTER TABLE `detection_result`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `detection_result`
--
ALTER TABLE `detection_result`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
