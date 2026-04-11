package com.screentime.tracker

import android.app.usage.UsageStats
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.drawable.Drawable
import java.util.*

class UsageTracker(private val context: Context) {

    private val usageStatsManager =
        context.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
    private val packageManager = context.packageManager

    data class AppUsageStat(
        val packageName: String,
        val appName: String,
        val totalTimeInForegroundSeconds: Long,
        val icon: Drawable? = null
    )

    /**
     * Gets today's screen time usage for all apps.
     */
    fun getTodaysUsage(): List<AppUsageStat> {
        val calendar = Calendar.getInstance()
        calendar.set(Calendar.HOUR_OF_DAY, 0)
        calendar.set(Calendar.MINUTE, 0)
        calendar.set(Calendar.SECOND, 0)
        calendar.set(Calendar.MILLISECOND, 0)
        val startTime = calendar.timeInMillis
        val endTime = System.currentTimeMillis()

        val stats = usageStatsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            startTime,
            endTime
        )

        val result = mutableListOf<AppUsageStat>()

        for (usageStats in stats) {
            if (usageStats.totalTimeInForeground > 0) {
                val appName = getAppName(usageStats.packageName)
                val icon = getAppIcon(usageStats.packageName)
                
                result.add(
                    AppUsageStat(
                        packageName = usageStats.packageName,
                        appName = appName,
                        totalTimeInForegroundSeconds = usageStats.totalTimeInForeground / 1000,
                        icon = icon
                    )
                )
            }
        }
        
        // Sort by most used
        return result.sortedByDescending { it.totalTimeInForegroundSeconds }
    }

    private fun getAppName(packageName: String): String {
        return try {
            val applicationInfo = packageManager.getApplicationInfo(packageName, 0)
            packageManager.getApplicationLabel(applicationInfo).toString()
        } catch (e: PackageManager.NameNotFoundException) {
            packageName
        }
    }

    private fun getAppIcon(packageName: String): Drawable? {
        return try {
            packageManager.getApplicationIcon(packageName)
        } catch (e: PackageManager.NameNotFoundException) {
            null
        }
    }
    
    /**
     * Helper to check if the user has granted the Usage Access permission
     */
    fun hasUsageStatsPermission(): Boolean {
        val calendar = Calendar.getInstance()
        calendar.add(Calendar.MINUTE, -1)
        val stats = usageStatsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            calendar.timeInMillis,
            System.currentTimeMillis()
        )
        return stats.isNotEmpty()
    }
}
