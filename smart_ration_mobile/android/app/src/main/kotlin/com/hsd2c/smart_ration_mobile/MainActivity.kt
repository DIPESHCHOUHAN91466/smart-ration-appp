package com.hsd2c.smart_ration_mobile

import android.app.Activity
import android.content.Intent
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/**
 * Adds one native feature: "Save as" for files the app creates (the person's data export).
 * Android's own file picker asks where to save, so the app needs no storage permission and
 * never leaves a copy in shared storage.
 */
class MainActivity : FlutterActivity() {
    private var pendingResult: MethodChannel.Result? = null
    private var pendingBytes: ByteArray? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "smart_ration/files").setMethodCallHandler { call, result ->
            if (call.method != "saveDocument") return@setMethodCallHandler result.notImplemented()
            if (pendingResult != null) return@setMethodCallHandler result.error("BUSY", "A save is already open.", null)
            val name = call.argument<String>("name")
            val mime = call.argument<String>("mimeType")
            val bytes = call.argument<ByteArray>("bytes")
            if (name == null || mime == null || bytes == null) return@setMethodCallHandler result.error("BAD_ARGS", null, null)
            pendingResult = result
            pendingBytes = bytes
            val intent = Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type = mime
                putExtra(Intent.EXTRA_TITLE, name)
            }
            @Suppress("DEPRECATION")
            startActivityForResult(intent, SAVE_REQUEST)
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        @Suppress("DEPRECATION")
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != SAVE_REQUEST) return
        val result = pendingResult ?: return
        val bytes = pendingBytes
        pendingResult = null
        pendingBytes = null
        val uri = data?.data
        if (resultCode != Activity.RESULT_OK || uri == null || bytes == null) return result.success(false) // cancelled
        try {
            contentResolver.openOutputStream(uri, "w")?.use { it.write(bytes) } ?: throw IllegalStateException("no stream")
            result.success(true)
        } catch (e: Exception) {
            result.error("WRITE_FAILED", null, null) // no details: the path or content could be personal
        }
    }

    private companion object {
        const val SAVE_REQUEST = 4711
    }
}
