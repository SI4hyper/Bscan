import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Barcode Scanner',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: FirstScreen(),
    );
  }
}

class FirstScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.lightBlue[50],
      body: Center(
        child: ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.white, // เปลี่ยน primary เป็น backgroundColor
          ),
          onPressed: () {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => SecondScreen()),
            );
          },
          child: Text('Capture'),
        ),
      ),
    );
  }
}

class SecondScreen extends StatefulWidget {
  @override
  _SecondScreenState createState() => _SecondScreenState();
}

class _SecondScreenState extends State<SecondScreen> {
  final MobileScannerController _scannerController = MobileScannerController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: Icon(Icons.arrow_back),
          onPressed: () {
            Navigator.pop(context);
          },
        ),
        title: Text('Scan Barcode'),
      ),
      body: MobileScanner(
        controller: _scannerController,
        onDetect: (BarcodeCapture barcodeCapture) {
          final barcodeValue = barcodeCapture.barcodes.first.rawValue ?? '';
          if (barcodeValue.isNotEmpty) {
            _fetchDataFromGoogleScript(barcodeValue);
          }
        },
      ),
    );
  }

  Future<void> _fetchDataFromGoogleScript(String barcodeValue) async {
    final url = 'https://script.google.com/macros/s/YOR_ID/exec?barcode=$barcodeValue';
    final response = await http.get(Uri.parse(url));

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      _showPopup(data);

      // รอ 3 วินาทีก่อนที่จะนำทางกลับไปยังหน้าแรก
      Future.delayed(Duration(seconds: 3), () {
        Navigator.popUntil(context, (route) => route.isFirst);
      });
    } else {
      _showError('Failed to fetch data');
    }
  }

  void _showPopup(Map<String, dynamic> data) {
    // ตรวจสอบว่ามีข้อมูลใน data['data'] หรือไม่
    if (data['data'] != null) {
      final productName = data['data']['productName'] ?? 'ไม่มีข้อมูล';
      final price = data['data']['price'] ?? 0;
      final expiryDate = data['data']['expiryDate'] ?? 'ไม่มีข้อมูล';

      showDialog(
        context: context,
        builder: (BuildContext context) {
          return AlertDialog(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(15.0),
            ),
            title: Text(
              'ข้อมูลสินค้า',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 24,
                color: Colors.blueAccent,
              ),
            ),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  _buildInfoRow('ชื่อสินค้า:', productName),
                  _buildInfoRow('ราคา:', '฿$price'),
                  _buildInfoRow('วันหมดอายุ:', _formatDate(expiryDate)),
                ],
              ),
            ),
            actions: [
              TextButton(
                child: Text('OK'),
                onPressed: () {
                  Navigator.of(context).pop();
                },
              ),
            ],
          );
        },
      );
    } else {
      _showError('ไม่พบข้อมูลสินค้า');
    }
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
          ),
          Expanded(
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: TextStyle(fontSize: 18),
            ),
          ),
        ],
      ),
    );
  }

  String _formatDate(String dateString) {
    DateTime dateTime = DateTime.parse(dateString);
    return '${dateTime.day}/${dateTime.month}/${dateTime.year}';
  }

  void _showError(String message) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Error'),
          content: Text(message),
          actions: [
            TextButton(
              child: Text('OK'),
              onPressed: () {
                Navigator.of(context).pop();
              },
            ),
          ],
        );
      },
    );
  }
}