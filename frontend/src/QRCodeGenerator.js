import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const QRCodeGenerator = () => {
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    company: '',
    title: '',
    url_work: '',
    url_home: ''
  });

  // QR code customization state
  const [qrSettings, setQrSettings] = useState({
    color: '#000000',
    primaryHue: 180,
    gradient: 100,
    markerShape: 'square',
    dotShape: 'square',
    logo: null,
    logoSize: 30
  });

  // UI state
  const [qrImage, setQrImage] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);

  // Color conversion functions
  const hslToHex = (h, s, l) => {
    l /= 100;
    const a = s * Math.min(l, 1 - l) / 100;
    const f = n => {
      const k = (n + h / 30) % 12;
      const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
      return Math.round(255 * color).toString(16).padStart(2, '0');
    };
    return `#${f(0)}${f(8)}${f(4)}`;
  };

  const hexToHsl = (hex) => {
    let r = parseInt(hex.slice(1, 3), 16) / 255;
    let g = parseInt(hex.slice(3, 5), 16) / 255;
    let b = parseInt(hex.slice(5, 7), 16) / 255;

    let max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h, s, l = (max + min) / 2;

    if (max === min) {
      h = s = 0;
    } else {
      let d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r: h = (g - b) / d + (g < b ? 6 : 0); break;
        case g: h = (b - r) / d + 2; break;
        case b: h = (r - g) / d + 4; break;
      }
      h /= 6;
    }

    return [h * 360, s * 100, l * 100];
  };

  // Update color based on sliders
  const updateColor = (primaryHue, gradientValue) => {
    let gradientLightness = gradientValue;
    if (gradientValue > 100) {
      gradientLightness = 100 + (gradientValue - 100) / 2;
    } else {
      gradientLightness = gradientValue / 2;
    }
    const color = hslToHex(primaryHue, 100, gradientLightness);
    setQrSettings(prev => ({ ...prev, color, primaryHue, gradient: gradientValue }));
  };

  // Handle form input changes
  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Handle QR settings changes
  const handleQrSettingsChange = (e) => {
    const { name, value } = e.target;
    setQrSettings(prev => ({ ...prev, [name]: value }));
  };

  // Handle logo upload
  const handleLogoUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setQrSettings(prev => ({ ...prev, logo: event.target.result }));
      };
      reader.readAsDataURL(file);
    }
  };

  // Handle hex color input
  const handleHexChange = (e) => {
    let hex = e.target.value;
    if (hex.charAt(0) !== '#') hex = '#' + hex;
    if (!/^#[0-9A-F]{6}$/i.test(hex)) return;

    const [h, s, l] = hexToHsl(hex);
    
    let gradientValue;
    if (l > 50) {
      gradientValue = 100 + (l - 50) * 2;
    } else {
      gradientValue = l * 2;
    }
    
    setQrSettings(prev => ({ 
      ...prev, 
      color: hex,
      primaryHue: h,
      gradient: gradientValue
    }));
  };

  // Generate QR code
  const generateQRCode = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const response = await axios.post(`${API}/qr-code`, {
        ...formData,
        color: qrSettings.color,
        marker_shape: qrSettings.markerShape,
        dot_shape: qrSettings.dotShape,
        logo_base64: qrSettings.logo,
        logo_size: qrSettings.logoSize
      });

      setQrImage(response.data.qr_image_base64);
    } catch (err) {
      setError('Erreur lors de la génération du QR code');
      console.error('Error generating QR code:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  // Download PNG
  const downloadPNG = () => {
    const firstName = formData.name.split(' ')[0] || 'QRCode';
    const lastName = formData.name.split(' ').slice(1).join('') || '';
    const filename = `${firstName}${lastName}FoxVelocityCreation.png`;

    const params = new URLSearchParams({
      name: formData.name,
      phone: formData.phone,
      email: formData.email,
      company: formData.company,
      title: formData.title,
      url_work: formData.url_work,
      url_home: formData.url_home,
      color: qrSettings.color,
      marker_shape: qrSettings.markerShape,
      dot_shape: qrSettings.dotShape,
      logo_size: qrSettings.logoSize.toString()
    });

    if (qrSettings.logo) {
      params.append('logo_base64', qrSettings.logo);
    }

    const link = document.createElement('a');
    link.href = `${API}/download-png?${params}`;
    link.download = filename;
    link.click();
  };

  // Download SVG
  const downloadSVG = () => {
    const firstName = formData.name.split(' ')[0] || 'QRCode';
    const lastName = formData.name.split(' ').slice(1).join('') || '';
    const filename = `${firstName}${lastName}FoxVelocityCreation.svg`;

    const params = new URLSearchParams({
      name: formData.name,
      phone: formData.phone,
      email: formData.email,
      company: formData.company,
      title: formData.title,
      url_work: formData.url_work,
      url_home: formData.url_home,
      color: qrSettings.color,
      marker_shape: qrSettings.markerShape,
      dot_shape: qrSettings.dotShape
    });

    const link = document.createElement('a');
    link.href = `${API}/download-svg?${params}`;
    link.download = filename;
    link.click();
  };

  // Update color when sliders change
  useEffect(() => {
    updateColor(qrSettings.primaryHue, qrSettings.gradient);
  }, [qrSettings.primaryHue, qrSettings.gradient]);

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">
            Générateur de QR Code Personnalisé
          </h2>

          {/* Form Fields */}
          <div className="space-y-4 mb-6">
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleFormChange}
              placeholder="Nom complet"
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleFormChange}
              placeholder="Numéro de téléphone"
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleFormChange}
              placeholder="Adresse e-mail"
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <input
              type="text"
              name="company"
              value={formData.company}
              onChange={handleFormChange}
              placeholder="Entreprise"
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleFormChange}
              placeholder="Titre/Poste"
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <input
              type="url"
              name="url_work"
              value={formData.url_work}
              onChange={handleFormChange}
              placeholder="Site Professionnel"
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <input
              type="url"
              name="url_home"
              value={formData.url_home}
              onChange={handleFormChange}
              placeholder="Site Réseaux Sociaux"
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Color Picker */}
          <div className="mb-6">
            <div 
              className="h-12 rounded-md mb-4 border border-gray-300"
              style={{ backgroundColor: qrSettings.color }}
            ></div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Couleur Primaire
                </label>
                <input
                  type="range"
                  min="0"
                  max="360"
                  value={qrSettings.primaryHue}
                  onChange={(e) => updateColor(parseInt(e.target.value), qrSettings.gradient)}
                  className="w-full h-3 bg-gradient-to-r from-red-500 via-yellow-500 via-green-500 via-cyan-500 via-blue-500 via-purple-500 to-red-500 rounded-lg appearance-none cursor-pointer"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dégradé
                </label>
                <input
                  type="range"
                  min="0"
                  max="200"
                  value={qrSettings.gradient}
                  onChange={(e) => updateColor(qrSettings.primaryHue, parseInt(e.target.value))}
                  className="w-full h-3 bg-gradient-to-r from-black to-white rounded-lg appearance-none cursor-pointer"
                />
              </div>
              
              <input
                type="text"
                value={qrSettings.color}
                onChange={handleHexChange}
                placeholder="#000000"
                className="w-full p-3 border border-gray-300 rounded-md text-center font-mono focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Logo Upload */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Ajouter un logo (PNG recommandé) :
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={handleLogoUpload}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            
            {qrSettings.logo && (
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Taille du logo : {qrSettings.logoSize}%
                </label>
                <input
                  type="range"
                  min="10"
                  max="40"
                  value={qrSettings.logoSize}
                  onChange={(e) => setQrSettings(prev => ({ ...prev, logoSize: parseInt(e.target.value) }))}
                  className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
              </div>
            )}
          </div>

          {/* Shape Options */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Forme des repères :
              </label>
              <select
                name="markerShape"
                value={qrSettings.markerShape}
                onChange={handleQrSettingsChange}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="square">Carrés</option>
                <option value="circle">Cercles</option>
                <option value="rounded">Arrondis</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Forme des points :
              </label>
              <select
                name="dotShape"
                value={qrSettings.dotShape}
                onChange={handleQrSettingsChange}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="square">Carrés</option>
                <option value="circle">Cercles</option>
                <option value="rounded">Arrondis</option>
              </select>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-4 mb-6">
            <button
              onClick={generateQRCode}
              disabled={isGenerating}
              className="flex-1 bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-md transition-colors duration-200"
            >
              {isGenerating ? 'Génération...' : 'Générer QR Code'}
            </button>
            
            <button
              onClick={downloadPNG}
              disabled={!qrImage}
              className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-md transition-colors duration-200"
            >
              Télécharger PNG
            </button>
            
            <button
              onClick={downloadSVG}
              disabled={!qrImage}
              className="flex-1 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-md transition-colors duration-200"
            >
              Télécharger SVG
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
              {error}
            </div>
          )}

          {/* QR Code Display */}
          {qrImage && (
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-800 mb-4">
                QR Code Généré
              </h3>
              <div className="inline-block p-4 bg-white border border-gray-300 rounded-lg">
                <img 
                  src={qrImage} 
                  alt="QR Code généré" 
                  className="max-w-full h-auto"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QRCodeGenerator;