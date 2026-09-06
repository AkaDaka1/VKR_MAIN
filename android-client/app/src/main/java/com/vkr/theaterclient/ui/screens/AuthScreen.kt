package com.vkr.theaterclient.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.vkr.theaterclient.ui.TheaterViewModel

@Composable
fun AuthScreen(
    viewModel: TheaterViewModel,
    onAuthenticated: () -> Unit,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    LaunchedEffect(state.authenticated) {
        if (state.authenticated) onAuthenticated()
    }

    var email by remember { mutableStateOf("mobile@example.com") }
    var phone by remember { mutableStateOf("+79990001122") }
    var password by remember { mutableStateOf("pass12345") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(text = "Вход клиента", style = MaterialTheme.typography.headlineSmall)
        if (!state.sessionChecked) {
            Text("Проверка сессии...")
        }

        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Email") },
        )
        OutlinedTextField(
            value = phone,
            onValueChange = { phone = it },
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Phone") },
        )
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Password") },
        )

        Button(
            onClick = { viewModel.login(email, password) },
            modifier = Modifier.fillMaxWidth(),
            enabled = state.sessionChecked && !state.loading,
        ) {
            Text("Войти")
        }
        Button(
            onClick = { viewModel.registerAndLogin(email, phone, password) },
            modifier = Modifier.fillMaxWidth(),
            enabled = state.sessionChecked && !state.loading,
        ) {
            Text("Зарегистрироваться")
        }

        if (state.loading) Text("Загрузка...")
        state.error?.let { Text(text = it, color = MaterialTheme.colorScheme.error) }
    }
}
