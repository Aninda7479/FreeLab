package com.screentime.tracker.sync

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import android.util.Log

class NsdHelper(context: Context) {

    private val nsdManager = context.getSystemService(Context.NSD_SERVICE) as NsdManager
    private val serviceType = "_screentime._tcp."
    private val TAG = "NsdHelper"

    private var discoveryListener: NsdManager.DiscoveryListener? = null
    
    interface SyncCallback {
        fun onWindowsPCFound(ip: String, port: Int)
        fun onSyncError(error: String)
    }

    fun discoverServices(callback: SyncCallback) {
        discoveryListener = object : NsdManager.DiscoveryListener {
            override fun onStartDiscoveryFailed(serviceType: String, errorCode: Int) {
                Log.e(TAG, "Discovery failed: Error code:$errorCode")
                nsdManager.stopServiceDiscovery(this)
                callback.onSyncError("Failed to start mDNS discovery")
            }

            override fun onStopDiscoveryFailed(serviceType: String, errorCode: Int) {
                Log.e(TAG, "Discovery failed: Error code:$errorCode")
                nsdManager.stopServiceDiscovery(this)
            }

            override fun onDiscoveryStarted(serviceType: String) {
                Log.d(TAG, "Service discovery started")
            }

            override fun onDiscoveryStopped(serviceType: String) {
                Log.i(TAG, "Discovery stopped: $serviceType")
            }

            override fun onServiceFound(serviceInfo: NsdServiceInfo) {
                Log.d(TAG, "Service discovery success: $serviceInfo")
                
                // Found our Windows PC ZeroConf broadcast!
                if (serviceInfo.serviceType.contains("screentime")) {
                    nsdManager.resolveService(serviceInfo, object : NsdManager.ResolveListener {
                        override fun onResolveFailed(serviceInfo: NsdServiceInfo, errorCode: Int) {
                            Log.e(TAG, "Resolve failed: $errorCode")
                        }

                        override fun onServiceResolved(serviceInfo: NsdServiceInfo) {
                            Log.d(TAG, "Resolve Succeeded. ${serviceInfo}")
                            val port = serviceInfo.port
                            val host = serviceInfo.host.hostAddress
                            // Notify UI/Worker to start HTTP POST to Windows
                            if (host != null) {
                                callback.onWindowsPCFound(host, port)
                            }
                        }
                    })
                }
            }

            override fun onServiceLost(serviceInfo: NsdServiceInfo) {
                Log.e(TAG, "service lost: $serviceInfo")
            }
        }
        
        nsdManager.discoverServices(serviceType, NsdManager.PROTOCOL_DNS_SD, discoveryListener)
    }

    fun stopDiscovery() {
        discoveryListener?.let { 
            nsdManager.stopServiceDiscovery(it) 
            discoveryListener = null
        }
    }
}
