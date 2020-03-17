package de.nanoimaging.uc2controller;

import android.app.Service;
import android.content.Intent;
import android.os.Environment;
import android.os.IBinder;
import android.support.annotation.Nullable;

import java.io.File;
import java.io.IOException;
import java.util.Properties;

import io.moquette.BrokerConstants;
import io.moquette.server.Server;
import io.moquette.server.config.MemoryConfig;

/**
 * Created by paula on 25/12/17.
 *
 * Start MQTT Broker / Port : 1887
 */

public class BrokerService extends Service {


    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Server server = new Server();
        try {
            MemoryConfig memoryConfig = new MemoryConfig(new Properties());
            memoryConfig.setProperty(BrokerConstants.PERSISTENT_STORE_PROPERTY_NAME,
                    Environment.getExternalStorageDirectory().getAbsolutePath() +
                            File.separator + BrokerConstants.DEFAULT_MOQUETTE_STORE_MAP_DB_FILENAME);
            server.startServer(memoryConfig);
        } catch (IOException e) {
            e.printStackTrace();
        }
        return START_STICKY;
    }
}
